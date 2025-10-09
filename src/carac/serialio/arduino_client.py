import time
from threading import Event, Lock, Thread
from typing import Callable

import serial
from loguru import logger

from ..config.settings import settings
from ..protocol.models import (
    CameraTriggerCommand,
    Command,
    ConnectionStatus,
    LightingSetCommand,
    Message,
    MessageType,
    MotorFlipCommand,
    MotorPositionCommand,
    PhotoSequenceStartCommand,
    Response,
    SystemEmergencyStopCommand,
    SystemPingCommand,
    SystemResetCommand,
    SystemStatusCommand,
    TestLedToggleCommand,
)
from .connection_monitor import AcknowledgmentInfo, ConnectionHealth, ConnectionMonitor


class ArduinoClient:
    DEFAULT_COMMAND_TIMEOUT = 2.0
    RECONNECT_DELAY = 0.5
    HANDSHAKE_DELAY = 0.2
    READ_LOOP_DELAY = 0.01
    THREAD_JOIN_TIMEOUT = 1.0
    COMMUNICATION_TEST_TIMEOUT = 5.0
    JSON_START_CHAR = "{"
    ACK_PREFIX = "ACK:"

    def __init__(self) -> None:
        self._serial: serial.Serial | None = None
        self._status = ConnectionStatus.DISCONNECTED
        self._lock = Lock()
        self._read_thread: Thread | None = None
        self._stop_reading = False
        self._response_callback: Callable[[Response], None] | None = None
        self._event_callback: Callable[[Message], None] | None = None
        self._pending_response: Response | None = None
        self._response_event = Event()
        self._command_timeout = self.DEFAULT_COMMAND_TIMEOUT

        self._connection_monitor = ConnectionMonitor()
        self._heartbeat_callback: Callable[[ConnectionHealth], None] | None = None
        self._ack_callback: Callable[[AcknowledgmentInfo], None] | None = None
    
    def connect(self, port: str, baud_rate: int | None = None) -> bool:
        if self._status == ConnectionStatus.CONNECTED:
            logger.warning("Already connected to Arduino")
            return True

        baud_rate = baud_rate or settings.default_baud_rate

        try:
            self._status = ConnectionStatus.CONNECTING
            logger.info(f"Connecting to Arduino on {port} at {baud_rate} baud")

            self._serial = self._create_serial_connection(port, baud_rate)
            time.sleep(self.RECONNECT_DELAY)

            if not self._serial.is_open:
                self._status = ConnectionStatus.ERROR
                logger.error("Failed to open serial connection")
                return False

            self._finalize_connection()
            return True

        except Exception as e:
            self._status = ConnectionStatus.ERROR
            logger.error(f"Error connecting to Arduino: {e}")
            return False

    def _create_serial_connection(self, port: str, baud_rate: int) -> serial.Serial:
        return serial.Serial(
            port=port,
            baudrate=baud_rate,
            timeout=settings.default_timeout,
            write_timeout=settings.default_timeout,
        )

    def _finalize_connection(self) -> None:
        self._status = ConnectionStatus.CONNECTED
        logger.info("Successfully connected to Arduino")
        self._start_reading()
        self._connection_monitor.start_monitoring()
        time.sleep(self.HANDSHAKE_DELAY)
    
    def disconnect(self) -> None:
        self._connection_monitor.stop_monitoring()

        with self._lock:
            if self._serial and self._serial.is_open:
                self._stop_read_thread()
                self._serial.close()
                logger.info("Disconnected from Arduino")

            self._reset_connection_state()

    def _stop_read_thread(self) -> None:
        self._stop_reading = True
        self._response_event.set()

        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=self.THREAD_JOIN_TIMEOUT)

    def _reset_connection_state(self) -> None:
        self._serial = None
        self._status = ConnectionStatus.DISCONNECTED
        self._pending_response = None
        self._response_event.clear()
    
    def send_command(self, command: Message | Command) -> Response | None:
        if not self._serial or not self._serial.is_open:
            logger.error("Not connected to ESP32")
            return None

        try:
            self._prepare_and_send_command(command)
            return self._wait_for_response()

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None

    def _prepare_and_send_command(self, command: Message | Command) -> None:
        with self._lock:
            self._pending_response = None
            self._response_event.clear()

            command_data = command.to_serial()
            logger.info(f"→ ESP32: {command_data.strip()}")

            self._connection_monitor.register_command_sent(command.type)

            self._serial.write(command_data.encode('utf-8'))
            self._serial.flush()

    def _wait_for_response(self) -> Response | None:
        if not self._response_event.wait(timeout=self._command_timeout):
            logger.warning("No response received from ESP32 within timeout")
            return None

        with self._lock:
            response = self._pending_response
            self._pending_response = None

            if response:
                logger.info(f"← ESP32: {response}")
                return response
            else:
                logger.warning("Response event triggered but no response data")
                return None
    
    def ping(self) -> bool:
        response = self.send_command(SystemPingCommand.create())
        return response is not None and response.success
    
    def test_communication(self) -> bool:
        if not self.is_connected:
            logger.warning("Cannot test communication - not connected")
            return False

        logger.info("Testing ESP32 communication...")
        original_timeout = self._command_timeout
        self._command_timeout = self.COMMUNICATION_TEST_TIMEOUT

        try:
            success = self.ping()
            self._log_test_result(success)
            return success
        finally:
            self._command_timeout = original_timeout

    def _log_test_result(self, success: bool) -> None:
        if success:
            logger.info("Communication test successful!")
        else:
            logger.warning("Communication test failed")
    
    def get_status(self) -> Response | None:
        return self.send_command(SystemStatusCommand.create())
    
    def set_lighting(self, channel: str, intensity: int) -> Response | None:
        return self.send_command(LightingSetCommand.create(channel, intensity))
    
    def start_photo_sequence(
        self,
        count: int = 5,
        delay: float = 1.0,
        auto_flip: bool = False
    ) -> Response | None:
        return self.send_command(
            PhotoSequenceStartCommand.create(count, delay, auto_flip)
        )
    
    def toggle_led(self) -> Response | None:
        return self.send_command(TestLedToggleCommand.create())
    
    def motor_position(self, direction: str, steps: int | None = None) -> Response | None:
        return self.send_command(MotorPositionCommand.create(direction, steps))
    
    def motor_flip(self) -> Response | None:
        return self.send_command(MotorFlipCommand.create())
    
    def camera_trigger(self, duration: int | None = None) -> Response | None:
        return self.send_command(CameraTriggerCommand.create(duration))
    
    def emergency_stop(self) -> Response | None:
        return self.send_command(SystemEmergencyStopCommand.create())
    
    def reset_system(self) -> Response | None:
        return self.send_command(SystemResetCommand.create())
    
    def set_response_callback(self, callback: Callable[[Response], None]) -> None:
        self._response_callback = callback
    
    def set_event_callback(self, callback: Callable[[Message], None]) -> None:
        self._event_callback = callback
    
    def set_heartbeat_callback(self, callback: Callable[[ConnectionHealth], None]) -> None:
        self._heartbeat_callback = callback
        self._connection_monitor.set_heartbeat_callback(callback)
    
    def set_ack_callback(self, callback: Callable[[AcknowledgmentInfo], None]) -> None:
        self._ack_callback = callback
        self._connection_monitor.set_ack_callback(callback)
    
    def get_connection_health(self) -> ConnectionHealth:
        return self._connection_monitor.get_health()
    
    def _start_reading(self) -> None:
        self._stop_reading = False
        self._read_thread = Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
    
    def _read_loop(self) -> None:
        while not self._stop_reading and self._serial and self._serial.is_open:
            try:
                self._process_serial_data()
                time.sleep(self.READ_LOOP_DELAY)

            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                time.sleep(self.READ_LOOP_DELAY)

        logger.debug("Read loop stopped")

    def _process_serial_data(self) -> None:
        if self._serial.in_waiting <= 0:
            return

        raw_bytes = self._serial.readline()
        data = self._decode_serial_data(raw_bytes)

        if not data:
            return

        logger.debug(f"RAW ESP32: {repr(data)}")

        if self._is_non_json_response(data):
            logger.debug(f"Ignoring non-JSON message: {data}")
            return

        message = Message.from_serial(data)
        logger.debug(f"Parsed message: type={message.type}")

        self._route_message(message)

    def _decode_serial_data(self, raw_bytes: bytes) -> str:
        try:
            return raw_bytes.decode('utf-8', errors='ignore').strip()
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode bytes: {raw_bytes.hex()}")
            return ""
    
    def _is_non_json_response(self, data: str) -> bool:
        return data.startswith(self.ACK_PREFIX) or not data.startswith(self.JSON_START_CHAR)
    
    def _route_message(self, message: Message) -> None:
        message_handlers = {
            MessageType.EVENT_HEARTBEAT: self._handle_heartbeat,
            MessageType.RESPONSE_ACK: self._handle_acknowledgment,
        }

        handler = message_handlers.get(message.type)
        if handler:
            handler(message)
            return

        if self._is_response_message(message):
            response = Response.from_message(message)
            self._route_response(response)
        elif self._is_event_message(message):
            self._route_event(message)
        else:
            logger.warning(f"Received unexpected message type: {message.type}")
    
    def _is_response_message(self, message: Message) -> bool:
        return message.type in [
            MessageType.RESPONSE_SUCCESS,
            MessageType.RESPONSE_ERROR,
            MessageType.RESPONSE_STATUS,
        ]
    
    def _is_event_message(self, message: Message) -> bool:
        return message.type.startswith("event_")
    
    def _route_response(self, response: Response) -> None:
        with self._lock:
            if not self._response_event.is_set() and self._pending_response is None:
                self._pending_response = response
                self._response_event.set()
                logger.debug("Response routed to synchronous command")
                return

        logger.debug("Response routed to async callback")
        self._notify_response_callback(response)

    def _notify_response_callback(self, response: Response) -> None:
        if self._response_callback:
            try:
                self._response_callback(response)
            except Exception as e:
                logger.error(f"Error in async response callback: {e}")
    
    def _route_event(self, event: Message) -> None:
        logger.info(f"Event received: {event.type}")
        self._notify_event_callback(event)

    def _notify_event_callback(self, event: Message) -> None:
        if self._event_callback:
            try:
                self._event_callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
        else:
            logger.debug(f"No event callback registered for: {event.type}")
    
    def _handle_heartbeat(self, message: Message) -> None:
        payload = message.payload
        uptime = payload.get("uptime", 0)
        status = payload.get("status", "unknown")
        
        self._connection_monitor.handle_heartbeat(uptime, status)
    
    def _handle_acknowledgment(self, message: Message) -> None:
        payload = message.payload
        received_type = payload.get("received_type", "unknown")
        timestamp = payload.get("timestamp", 0)
        
        self._connection_monitor.handle_acknowledgment(received_type, timestamp)
    
    @property
    def is_connected(self) -> bool:
        return (
            self._status == ConnectionStatus.CONNECTED and
            self._serial is not None and
            self._serial.is_open
        )
    
    @property
    def status(self) -> ConnectionStatus:
        return self._status
    
    def __enter__(self) -> "ArduinoClient":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
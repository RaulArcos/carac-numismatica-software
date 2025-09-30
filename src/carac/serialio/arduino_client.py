import time
from typing import Callable
from threading import Thread, Lock, Event

import serial
from loguru import logger

from ..config.settings import settings
from ..protocol.models import (
    Command,
    Response,
    ConnectionStatus,
    PingCommand,
    StatusCommand,
    LightingCommand,
    PhotoSequenceCommand,
    LedToggleCommand,
)


class ArduinoClient:
    DEFAULT_COMMAND_TIMEOUT = 2.0
    RECONNECT_DELAY = 0.5
    HANDSHAKE_DELAY = 0.2
    READ_LOOP_DELAY = 0.01
    
    def __init__(self) -> None:
        self._serial: serial.Serial | None = None
        self._status = ConnectionStatus.DISCONNECTED
        self._lock = Lock()
        self._read_thread: Thread | None = None
        self._stop_reading = False
        self._response_callback: Callable[[Response], None] | None = None
        self._pending_response: Response | None = None
        self._response_event = Event()
        self._command_timeout = self.DEFAULT_COMMAND_TIMEOUT
    
    def connect(self, port: str, baud_rate: int | None = None) -> bool:
        if self._status == ConnectionStatus.CONNECTED:
            logger.warning("Already connected to Arduino")
            return True
        
        baud_rate = baud_rate or settings.default_baud_rate
        
        try:
            self._status = ConnectionStatus.CONNECTING
            logger.info(f"Connecting to Arduino on {port} at {baud_rate} baud")
            
            self._serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=settings.default_timeout,
                write_timeout=settings.default_timeout,
            )
            
            time.sleep(self.RECONNECT_DELAY)
            
            if self._serial.is_open:
                self._status = ConnectionStatus.CONNECTED
                logger.info("Successfully connected to Arduino")
                self._start_reading()
                time.sleep(self.HANDSHAKE_DELAY)
                return True
            else:
                self._status = ConnectionStatus.ERROR
                logger.error("Failed to open serial connection")
                return False
                
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            logger.error(f"Error connecting to Arduino: {e}")
            return False
    
    def disconnect(self) -> None:
        with self._lock:
            if self._serial and self._serial.is_open:
                self._stop_reading = True
                self._response_event.set()
                
                if self._read_thread and self._read_thread.is_alive():
                    self._read_thread.join(timeout=1.0)
                
                self._serial.close()
                logger.info("Disconnected from Arduino")
            
            self._serial = None
            self._status = ConnectionStatus.DISCONNECTED
            self._pending_response = None
            self._response_event.clear()
    
    def send_command(self, command: Command) -> Response | None:
        if not self._serial or not self._serial.is_open:
            logger.error("Not connected to Arduino")
            return None
        
        try:
            with self._lock:
                self._pending_response = None
                self._response_event.clear()
                
                command_data = command.to_serial()
                logger.info(f"Sending command: {command_data.strip()}")
                
                self._serial.write(command_data.encode('utf-8'))
                self._serial.flush()
            
            if self._response_event.wait(timeout=self._command_timeout):
                with self._lock:
                    response = self._pending_response
                    self._pending_response = None
                    if response:
                        logger.info(f"Received response: {response}")
                        return response
                    else:
                        logger.warning("Response event triggered but no response data")
                        return None
            else:
                logger.warning("No response received from Arduino within timeout")
                return None
                    
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def ping(self) -> bool:
        response = self.send_command(PingCommand())
        return response is not None and response.success
    
    def test_communication(self) -> bool:
        if not self.is_connected:
            logger.warning("Cannot test communication - not connected")
            return False
        
        logger.info("Testing Arduino communication...")
        original_timeout = self._command_timeout
        self._command_timeout = 5.0
        
        try:
            success = self.ping()
            if success:
                logger.info("Communication test successful!")
            else:
                logger.warning("Communication test failed")
            return success
        finally:
            self._command_timeout = original_timeout
    
    def get_status(self) -> Response | None:
        return self.send_command(StatusCommand())
    
    def set_lighting(self, channel: str, intensity: int) -> Response | None:
        return self.send_command(LightingCommand(channel=channel, intensity=intensity))
    
    def start_photo_sequence(self, count: int = 5, delay: float = 1.0) -> Response | None:
        return self.send_command(PhotoSequenceCommand(count=count, delay=delay))
    
    def toggle_led(self) -> Response | None:
        return self.send_command(LedToggleCommand())
    
    def set_response_callback(self, callback: Callable[[Response], None]) -> None:
        self._response_callback = callback
    
    def _start_reading(self) -> None:
        self._stop_reading = False
        self._read_thread = Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
    
    def _read_loop(self) -> None:
        while not self._stop_reading and self._serial and self._serial.is_open:
            try:
                if self._serial.in_waiting > 0:
                    data = self._serial.readline().decode('utf-8').strip()
                    if data:
                        logger.info(f"RAW Arduino response: {repr(data)}")
                        
                        if data.startswith('ACK:') or not data.startswith('{'):
                            logger.debug(f"Ignoring non-JSON response: {data}")
                            continue
                        
                        response = Response.from_serial(data)
                        logger.debug(f"Parsed response: {response}")
                        self._route_response(response)
                
                time.sleep(self.READ_LOOP_DELAY)
                
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                break
        
        logger.debug("Read loop stopped")
    
    def _route_response(self, response: Response) -> None:
        with self._lock:
            if not self._response_event.is_set() and self._pending_response is None:
                self._pending_response = response
                self._response_event.set()
                logger.info("Response routed to synchronous command")
                return
        
        logger.info("Response routed to async callback")
        if self._response_callback:
            try:
                self._response_callback(response)
            except Exception as e:
                logger.error(f"Error in async response callback: {e}")
    
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
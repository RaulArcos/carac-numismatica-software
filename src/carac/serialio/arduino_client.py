import time
from typing import Optional, Callable
from threading import Thread, Lock, Event
from queue import Queue, Empty

import serial
from loguru import logger

from ..config.settings import settings
from ..protocol.models import (
    Command,
    Response,
    ConnectionStatus,
    PingCommand,
    StatusCommand,
)


class ArduinoClient:
    def __init__(self) -> None:
        self.serial: Optional[serial.Serial] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.lock = Lock()
        self._read_thread: Optional[Thread] = None
        self._stop_reading = False
        self._response_callback: Optional[Callable[[Response], None]] = None
        
        self._pending_response: Optional[Response] = None
        self._response_event = Event()
        self._command_timeout = 2.0 

        
        
    def connect(self, port: str, baud_rate: Optional[int] = None) -> bool:
        if self.status == ConnectionStatus.CONNECTED:
            logger.warning("Already connected to Arduino")
            return True
            
        baud_rate = baud_rate or settings.default_baud_rate
        
        try:
            self.status = ConnectionStatus.CONNECTING
            logger.info(f"Connecting to Arduino on {port} at {baud_rate} baud")
            
            self.serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=settings.default_timeout,
                write_timeout=settings.default_timeout,
            )
            
            time.sleep(0.5)
            
            if self.serial.is_open:
                self.status = ConnectionStatus.CONNECTED
                logger.info("Successfully connected to Arduino")
                
                self._start_reading()
                
                # Just wait a short time for initial ready message
                time.sleep(0.2)
                
                # Don't do ping during connection to avoid UI blocking
                # Ping will be done separately if needed
                logger.info("Connection established, ping will be tested separately")
                return True
            else:
                self.status = ConnectionStatus.ERROR
                logger.error("Failed to open serial connection")
                return False
                
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            logger.error(f"Error connecting to Arduino: {e}")
            return False
    
    def disconnect(self) -> None:
        with self.lock:
            if self.serial and self.serial.is_open:
                self._stop_reading = True
                
                # Signal any waiting commands to abort
                self._response_event.set()
                
                if self._read_thread and self._read_thread.is_alive():
                    self._read_thread.join(timeout=1.0)
                
                self.serial.close()
                logger.info("Disconnected from Arduino")
            
            self.serial = None
            self.status = ConnectionStatus.DISCONNECTED
            
            # Reset response handling state
            self._pending_response = None
            self._response_event.clear()
    
    def send_command(self, command: Command) -> Optional[Response]:
        if not self.serial or not self.serial.is_open:
            logger.error("Not connected to Arduino")
            return None
        
        try:
            with self.lock:
                # Clear any previous response and reset event
                self._pending_response = None
                self._response_event.clear()
                logger.debug("Cleared pending response and event before sending command")
                
                command_data = command.to_serial()
                logger.info(f"Sending command: {command_data.strip()}")
                
                self.serial.write(command_data.encode('utf-8'))
                self.serial.flush()
                
                logger.debug(f"Command sent, waiting for response (timeout: {self._command_timeout}s)")
                
            # Release lock while waiting to allow response processing
            logger.debug(f"Waiting for response event (timeout: {self._command_timeout}s)")
            if self._response_event.wait(timeout=self._command_timeout):
                with self.lock:
                    logger.debug("Event triggered, checking for response")
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
                with self.lock:
                    logger.debug(f"Final event state: {self._response_event.is_set()}, pending: {self._pending_response}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def ping(self) -> bool:
        command = PingCommand()
        response = self.send_command(command)
        return response is not None and response.success
    
    def test_communication(self) -> bool:
        """Test communication with Arduino after connection"""
        if not self.is_connected:
            logger.warning("Cannot test communication - not connected")
            return False
            
        logger.info("Testing Arduino communication...")
        
        # Try ping with a longer timeout for testing
        original_timeout = self._command_timeout
        self._command_timeout = 5.0  # 5 second timeout for testing
        
        try:
            success = self.ping()
            if success:
                logger.info("Communication test successful!")
            else:
                logger.warning("Communication test failed")
            return success
        finally:
            self._command_timeout = original_timeout
    
    def get_status(self) -> Optional[Response]:
        command = StatusCommand()
        return self.send_command(command)
    
    def set_lighting(self, channel: str, intensity: int) -> Optional[Response]:
        from ..protocol.models import LightingCommand
        
        command = LightingCommand(channel=channel, intensity=intensity)
        return self.send_command(command)
    
    def start_photo_sequence(self, count: int = 5, delay: float = 1.0) -> Optional[Response]:
        from ..protocol.models import PhotoSequenceCommand
        
        command = PhotoSequenceCommand(count=count, delay=delay)
        return self.send_command(command)
    
    def toggle_led(self) -> Optional[Response]:
        from ..protocol.models import LedToggleCommand
        
        command = LedToggleCommand()
        return self.send_command(command)
    
    def set_response_callback(self, callback: Callable[[Response], None]) -> None:
        self._response_callback = callback
    
    def _start_reading(self) -> None:
        self._stop_reading = False
        self._read_thread = Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
    
    def _read_loop(self) -> None:
        while not self._stop_reading and self.serial and self.serial.is_open:
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.readline().decode('utf-8').strip()
                    if data:
                        # Log the raw data for debugging
                        logger.info(f"RAW Arduino response: {repr(data)}")
                        
                        # Skip ACK messages and other non-JSON responses
                        if data.startswith('ACK:') or not data.startswith('{'):
                            logger.debug(f"Ignoring non-JSON response: {data}")
                            continue
                        
                        response = Response.from_serial(data)
                        logger.debug(f"Parsed response: {response}")
                        
                        # Route response appropriately
                        self._route_response(response)
                
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                break
        
        logger.debug("Read loop stopped")
    
    def _route_response(self, response: Response) -> None:
        """Route response to either synchronous command waiter or async callback"""
        # Check if we have a pending synchronous command waiting for response
        with self.lock:
            event_is_set = self._response_event.is_set()
            has_pending_response = self._pending_response is not None
            
            logger.debug(f"Routing response - event_set: {event_is_set}, has_pending: {has_pending_response}, response: {response}")
            
            if not event_is_set and not has_pending_response:
                # This might be for a synchronous command
                self._pending_response = response
                logger.debug(f"Setting pending response: {response}")
                self._response_event.set()
                logger.info("Response routed to synchronous command")
                logger.debug(f"Event set, event_is_set now: {self._response_event.is_set()}")
                return
        
        # This is an async response (like status updates or unsolicited messages)
        logger.info("Response routed to async callback")
        if self._response_callback:
            try:
                self._response_callback(response)
            except Exception as e:
                logger.error(f"Error in async response callback: {e}")
        else:
            logger.debug("No async callback registered, response discarded")
    
    @property
    def is_connected(self) -> bool:
        return (
            self.status == ConnectionStatus.CONNECTED and
            self.serial is not None and
            self.serial.is_open
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

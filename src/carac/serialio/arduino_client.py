import time
from typing import Optional, Callable
from threading import Thread, Lock

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
                
                if self.ping():
                    return True
                else:
                    logger.warning("Ping failed, but connection established")
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
                
                if self._read_thread and self._read_thread.is_alive():
                    self._read_thread.join(timeout=1.0)
                
                self.serial.close()
                logger.info("Disconnected from Arduino")
            
            self.serial = None
            self.status = ConnectionStatus.DISCONNECTED
    
    def send_command(self, command: Command) -> Optional[Response]:
        if not self.serial or not self.serial.is_open:
            logger.error("Not connected to Arduino")
            return None
        
        with self.lock:
            try:
                command_data = command.to_serial()
                logger.debug(f"Sending command: {command_data.strip()}")
                
                self.serial.write(command_data.encode('utf-8'))
                self.serial.flush()
                
                response_data = self.serial.readline().decode('utf-8').strip()
                
                if response_data:
                    response = Response.from_serial(response_data)
                    logger.debug(f"Received response: {response}")
                    return response
                else:
                    logger.warning("No response received from Arduino")
                    return None
                    
            except Exception as e:
                logger.error(f"Error sending command: {e}")
                return None
    
    def ping(self) -> bool:
        command = PingCommand()
        response = self.send_command(command)
        return response is not None and response.success
    
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
                        response = Response.from_serial(data)
                        logger.debug(f"Async response: {response}")
                        
                        if self._response_callback:
                            self._response_callback(response)
                
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                break
        
        logger.debug("Read loop stopped")
    
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

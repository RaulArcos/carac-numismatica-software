from typing import Dict, Optional, Callable
from dataclasses import dataclass

from loguru import logger

from ..config.settings import settings
from ..serialio.arduino_client import ArduinoClient
from ..protocol.models import Response, ConnectionStatus


@dataclass
class LightingState:
    channel: str
    intensity: int = 0
    enabled: bool = False


class SessionController:
    def __init__(self) -> None:
        self.arduino_client = ArduinoClient()
        self.lighting_states: Dict[str, LightingState] = {}
        self.connection_status = ConnectionStatus.DISCONNECTED
        self._status_callbacks: list[Callable[[ConnectionStatus], None]] = []
        self._response_callbacks: list[Callable[[Response], None]] = []
        
        for channel in settings.lighting_channels:
            self.lighting_states[channel] = LightingState(channel=channel)
        
        self.arduino_client.set_response_callback(self._handle_response)
    
    def connect(self, port: str, baud_rate: Optional[int] = None) -> bool:
        success = self.arduino_client.connect(port, baud_rate)
        self.connection_status = self.arduino_client.status
        self._notify_status_change()
        
        if success:
            logger.info(f"Connected to Arduino on {port}")
        else:
            logger.error(f"Failed to connect to Arduino on {port}")
        
        return success
    
    def disconnect(self) -> None:
        self.arduino_client.disconnect()
        self.connection_status = ConnectionStatus.DISCONNECTED
        self._notify_status_change()
        logger.info("Disconnected from Arduino")
    
    def set_lighting(self, channel: str, intensity: int) -> bool:
        if not self.arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        if channel not in self.lighting_states:
            logger.error(f"Unknown lighting channel: {channel}")
            return False
        
        intensity = max(0, min(intensity, settings.max_lighting_intensity))
        
        self.lighting_states[channel].intensity = intensity
        self.lighting_states[channel].enabled = intensity > 0
        
        response = self.arduino_client.set_lighting(channel, intensity)
        
        if response and response.success:
            logger.info(f"Set {channel} lighting to {intensity}")
            return True
        else:
            logger.error(f"Failed to set {channel} lighting to {intensity}")
            return False
    
    def get_lighting_state(self, channel: str) -> Optional[LightingState]:
        return self.lighting_states.get(channel)
    
    def get_all_lighting_states(self) -> Dict[str, LightingState]:
        return self.lighting_states.copy()
    
    def start_photo_sequence(self, count: Optional[int] = None, delay: Optional[float] = None) -> bool:
        if not self.arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        count = count or settings.photo_sequence_count
        delay = delay or settings.photo_sequence_delay
        
        response = self.arduino_client.start_photo_sequence(count, delay)
        
        if response and response.success:
            logger.info(f"Started photo sequence: {count} photos, {delay}s delay")
            return True
        else:
            logger.error("Failed to start photo sequence")
            return False
    
    def ping(self) -> bool:
        if not self.arduino_client.is_connected:
            return False
        
        return self.arduino_client.ping()
    
    def get_status(self) -> Optional[Response]:
        if not self.arduino_client.is_connected:
            return None
        
        return self.arduino_client.get_status()
    
    def toggle_led(self) -> bool:
        if not self.arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        response = self.arduino_client.toggle_led()
        
        if response and response.success:
            logger.info("LED toggled successfully")
            return True
        else:
            logger.error("Failed to toggle LED")
            return False
    
    def add_status_callback(self, callback: Callable[[ConnectionStatus], None]) -> None:
        self._status_callbacks.append(callback)
    
    def add_response_callback(self, callback: Callable[[Response], None]) -> None:
        self._response_callbacks.append(callback)
    
    def _handle_response(self, response: Response) -> None:
        logger.debug(f"Handling response: {response}")
        
        for callback in self._response_callbacks:
            try:
                callback(response)
            except Exception as e:
                logger.error(f"Error in response callback: {e}")
    
    def _notify_status_change(self) -> None:
        for callback in self._status_callbacks:
            try:
                callback(self.connection_status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    @property
    def is_connected(self) -> bool:
        return self.arduino_client.is_connected
    
    @property
    def current_status(self) -> ConnectionStatus:
        return self.connection_status

from dataclasses import dataclass

from loguru import logger

from ..config.settings import settings
from ..serialio.arduino_client import ArduinoClient
from ..serialio.connection_monitor import ConnectionHealth, AcknowledgmentInfo
from ..protocol.models import Response, ConnectionStatus, Message
from .callback_manager import CallbackManager


@dataclass
class LightingState:
    channel: str
    intensity: int = 0
    enabled: bool = False


class SessionController:
    def __init__(self) -> None:
        self._arduino_client = ArduinoClient()
        self._lighting_states: dict[str, LightingState] = {}
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._status_callbacks = CallbackManager[ConnectionStatus]()
        self._response_callbacks = CallbackManager[Response]()
        self._event_callbacks = CallbackManager[Message]()
        self._heartbeat_callbacks = CallbackManager[ConnectionHealth]()
        self._ack_callbacks = CallbackManager[AcknowledgmentInfo]()
        
        self._initialize_lighting_states()
        self._arduino_client.set_response_callback(self._handle_response)
        self._arduino_client.set_event_callback(self._handle_event)
        self._arduino_client.set_heartbeat_callback(self._handle_heartbeat)
        self._arduino_client.set_ack_callback(self._handle_acknowledgment)
    
    def _initialize_lighting_states(self) -> None:
        for channel in settings.lighting_channels:
            self._lighting_states[channel] = LightingState(channel=channel)
    
    def connect(self, port: str, baud_rate: int | None = None) -> bool:
        success = self._arduino_client.connect(port, baud_rate)
        self._update_connection_status(self._arduino_client.status)
        
        if success:
            logger.info(f"Connected to Arduino on {port}")
        else:
            logger.error(f"Failed to connect to Arduino on {port}")
        
        return success
    
    def disconnect(self) -> None:
        self._arduino_client.disconnect()
        self._update_connection_status(ConnectionStatus.DISCONNECTED)
        logger.info("Disconnected from Arduino")
    
    def set_lighting(self, channel: str, intensity: int) -> bool:
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        if channel not in self._lighting_states:
            logger.error(f"Unknown lighting channel: {channel}")
            return False
        
        intensity = max(0, min(intensity, settings.max_lighting_intensity))
        
        self._lighting_states[channel].intensity = intensity
        self._lighting_states[channel].enabled = intensity > 0
        
        response = self._arduino_client.set_lighting(channel, intensity)
        
        if response and response.success:
            logger.info(f"Set {channel} lighting to {intensity}")
            return True
        else:
            logger.error(f"Failed to set {channel} lighting to {intensity}")
            return False
    
    def get_lighting_state(self, channel: str) -> LightingState | None:
        return self._lighting_states.get(channel)
    
    def get_all_lighting_states(self) -> dict[str, LightingState]:
        return self._lighting_states.copy()
    
    def start_photo_sequence(
        self,
        count: int | None = None,
        delay: float | None = None
    ) -> bool:
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        count = count or settings.photo_sequence_count
        delay = delay or settings.photo_sequence_delay
        
        response = self._arduino_client.start_photo_sequence(count, delay)
        
        if response and response.success:
            logger.info(f"Started photo sequence: {count} photos, {delay}s delay")
            return True
        else:
            logger.error("Failed to start photo sequence")
            return False
    
    def ping(self) -> bool:
        if not self._arduino_client.is_connected:
            return False
        return self._arduino_client.ping()
    
    def test_communication(self) -> bool:
        return self._arduino_client.test_communication()
    
    def get_status(self) -> Response | None:
        if not self._arduino_client.is_connected:
            return None
        return self._arduino_client.get_status()
    
    def toggle_led(self) -> Response | None:
        """Toggle built-in LED for testing."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return None
        
        response = self._arduino_client.toggle_led()
        
        if response and response.success:
            logger.info("LED toggled successfully")
            return response
        else:
            logger.error("Failed to toggle LED")
            return None
    
    def motor_position(self, direction: str, steps: int | None = None) -> bool:
        """Move positioning motor forward or backward."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        
        response = self._arduino_client.motor_position(direction, steps)
        
        if response and response.success:
            logger.info(f"Motor moved {direction}")
            return True
        else:
            logger.error(f"Failed to move motor {direction}")
            return False
    
    def motor_flip(self) -> bool:
        """Flip the coin."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        
        response = self._arduino_client.motor_flip()
        
        if response and response.success:
            logger.info("Coin flipped successfully")
            return True
        else:
            logger.error("Failed to flip coin")
            return False
    
    def camera_trigger(self, duration: int | None = None) -> bool:
        """Trigger camera shutter."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        
        response = self._arduino_client.camera_trigger(duration)
        
        if response and response.success:
            logger.info("Camera triggered successfully")
            return True
        else:
            logger.error("Failed to trigger camera")
            return False
    
    def emergency_stop(self) -> bool:
        """Emergency stop - halt all operations."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        
        response = self._arduino_client.emergency_stop()
        
        if response and response.success:
            logger.info("Emergency stop executed")
            return True
        else:
            logger.error("Failed to execute emergency stop")
            return False
    
    def add_status_callback(self, callback) -> None:
        """Add callback for connection status changes."""
        self._status_callbacks.add(callback)
    
    def add_response_callback(self, callback) -> None:
        """Add callback for async responses."""
        self._response_callbacks.add(callback)
    
    def add_event_callback(self, callback) -> None:
        """Add callback for async events from ESP32."""
        self._event_callbacks.add(callback)
    
    def add_heartbeat_callback(self, callback) -> None:
        """Add callback for heartbeat events."""
        self._heartbeat_callbacks.add(callback)
    
    def add_ack_callback(self, callback) -> None:
        """Add callback for acknowledgment events."""
        self._ack_callbacks.add(callback)
    
    def get_connection_health(self) -> ConnectionHealth:
        """Get current connection health status."""
        return self._arduino_client.get_connection_health()
    
    def _handle_response(self, response: Response) -> None:
        logger.debug(f"Handling async response: {response}")
        self._response_callbacks.notify(response)
    
    def _handle_event(self, event: Message) -> None:
        logger.info(f"Handling event: {event.type}")
        self._event_callbacks.notify(event)
    
    def _handle_heartbeat(self, health: ConnectionHealth) -> None:
        """Handle heartbeat from ESP32."""
        logger.debug(f"Heartbeat received - alive: {health.is_alive}, uptime: {health.esp32_uptime_ms}ms")
        self._heartbeat_callbacks.notify(health)
    
    def _handle_acknowledgment(self, ack: AcknowledgmentInfo) -> None:
        """Handle acknowledgment from ESP32."""
        logger.debug(f"ACK received - type: {ack.received_type}, RTT: {ack.round_trip_ms:.1f}ms")
        self._ack_callbacks.notify(ack)
    
    def _update_connection_status(self, status: ConnectionStatus) -> None:
        self._connection_status = status
        self._status_callbacks.notify(status)
    
    @property
    def is_connected(self) -> bool:
        return self._arduino_client.is_connected
    
    @property
    def current_status(self) -> ConnectionStatus:
        return self._connection_status
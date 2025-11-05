from dataclasses import dataclass
from typing import Callable

from loguru import logger

from ..config.settings import settings
from ..protocol.models import ConnectionStatus, Message, Response
from ..serialio.arduino_client import ArduinoClient
from ..serialio.connection_monitor import AcknowledgmentInfo, ConnectionHealth
from .callback_manager import CallbackManager


@dataclass
class LightingState:
    channel: str
    intensity: int = 0
    enabled: bool = False


class SessionController:
    _VALID_CHANNELS = ["ring_1", "ring_2", "ring_3", "ring_4"]
    
    def __init__(self) -> None:
        self._arduino_client = ArduinoClient()
        self._lighting_states: dict[str, LightingState] = {}
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._status_callbacks = CallbackManager[ConnectionStatus]()
        self._response_callbacks = CallbackManager[Response]()
        self._event_callbacks = CallbackManager[Message]()
        self._heartbeat_callbacks = CallbackManager[ConnectionHealth]()
        self._ack_callbacks = CallbackManager[AcknowledgmentInfo]()

        for channel in settings.lighting_channels:
            self._lighting_states[channel] = LightingState(channel=channel)

        self._arduino_client.set_response_callback(self._handle_response)
        self._arduino_client.set_event_callback(self._handle_event)
        self._arduino_client.set_heartbeat_callback(self._handle_heartbeat)
        self._arduino_client.set_ack_callback(self._handle_acknowledgment)
    
    def connect(self, port: str, baud_rate: int | None = None) -> bool:
        success = self._arduino_client.connect(port, baud_rate)
        self._update_connection_status(self._arduino_client.status)
        if success:
            logger.info(f"Connected to Arduino on {port}")
        else:
            logger.info(f"Failed to connect to Arduino on {port}")
        return success

    def disconnect(self) -> None:
        self._arduino_client.disconnect()
        self._update_connection_status(ConnectionStatus.DISCONNECTED)
        logger.info("Disconnected from Arduino")
    
    def set_lighting(self, channel: str, intensity: int) -> bool:
        """Set lighting synchronously (waits for response). Use set_lighting_async for non-blocking."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        if channel not in self._VALID_CHANNELS:
            logger.error(f"Invalid lighting channel: {channel}. Expected one of {self._VALID_CHANNELS}")
            return False

        if channel not in self._lighting_states:
            self._lighting_states[channel] = LightingState(channel=channel)

        intensity = max(0, min(intensity, settings.max_lighting_intensity))
        self._lighting_states[channel].intensity = intensity
        self._lighting_states[channel].enabled = intensity > 0

        response = self._arduino_client.set_lighting(channel, intensity)
        success = response and response.success
        if success:
            logger.info(f"Set {channel} lighting to {intensity}")
        else:
            logger.info(f"Failed to set {channel} lighting to {intensity}")
        return success
    
    def set_lighting_async(self, channel: str, intensity: int) -> bool:
        """Set lighting asynchronously (non-blocking, optimistic update)."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        if channel not in self._VALID_CHANNELS:
            logger.error(f"Invalid lighting channel: {channel}. Expected one of {self._VALID_CHANNELS}")
            return False

        if channel not in self._lighting_states:
            self._lighting_states[channel] = LightingState(channel=channel)

        intensity = max(0, min(intensity, settings.max_lighting_intensity))
        # Update state optimistically (before ESP32 confirms)
        self._lighting_states[channel].intensity = intensity
        self._lighting_states[channel].enabled = intensity > 0

        # Send command without waiting for response
        sent = self._arduino_client.set_lighting_async(channel, intensity)
        if sent:
            logger.debug(f"Sent {channel} lighting command to {intensity} (async)")
        else:
            logger.warning(f"Failed to send {channel} lighting command")
        return sent
    
    def set_sections(self, sections: dict[str, int]) -> bool:
        """Set sections synchronously (waits for response). Use set_sections_async for non-blocking."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        clamped_sections = {}
        for section, intensity in sections.items():
            if section not in self._lighting_states:
                logger.error(f"Unknown lighting channel: {section}")
                return False
            clamped_intensity = max(0, min(intensity, settings.max_lighting_intensity))
            clamped_sections[section] = clamped_intensity
            self._lighting_states[section].intensity = clamped_intensity
            self._lighting_states[section].enabled = clamped_intensity > 0
        
        response = self._arduino_client.set_sections(clamped_sections)
        success = response and response.success
        if success:
            logger.info(f"Set sections lighting: {clamped_sections}")
        else:
            logger.info("Failed to set sections lighting")
        return success
    
    def set_sections_async(self, sections: dict[str, int]) -> bool:
        """Set sections asynchronously (non-blocking, optimistic update)."""
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False
        
        clamped_sections = {}
        for section, intensity in sections.items():
            if section not in self._lighting_states:
                logger.error(f"Unknown lighting channel: {section}")
                return False
            clamped_intensity = max(0, min(intensity, settings.max_lighting_intensity))
            clamped_sections[section] = clamped_intensity
            # Update state optimistically (before ESP32 confirms)
            self._lighting_states[section].intensity = clamped_intensity
            self._lighting_states[section].enabled = clamped_intensity > 0
        
        # Send command without waiting for response
        sent = self._arduino_client.set_sections_async(clamped_sections)
        if sent:
            logger.debug(f"Sent sections lighting command (async): {clamped_sections}")
        else:
            logger.warning("Failed to send sections lighting command")
        return sent
    
    def get_lighting_state(self, channel: str) -> LightingState | None:
        return self._lighting_states.get(channel)
    
    def get_all_lighting_states(self) -> dict[str, LightingState]:
        return self._lighting_states.copy()
    
    def start_photo_sequence(self, count: int | None = None, delay: float | None = None) -> bool:
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to Arduino")
            return False

        final_count = count or settings.photo_sequence_count
        final_delay = delay or settings.photo_sequence_delay
        response = self._arduino_client.start_photo_sequence(final_count, final_delay)
        success = response and response.success
        if success:
            logger.info(f"Started photo sequence: {final_count} photos, {final_delay}s delay")
        else:
            logger.info("Failed to start photo sequence")
        return success
    
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
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return None
        response = self._arduino_client.toggle_led()
        if response and response.success:
            logger.info("LED toggled successfully")
            return response
        logger.info("Failed to toggle LED")
        return None

    def motor_position(self, direction: str, steps: int | None = None) -> bool:
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        response = self._arduino_client.motor_position(direction, steps)
        success = response and response.success
        if success:
            logger.info(f"Motor moved {direction}")
        else:
            logger.info(f"Failed to move motor {direction}")
        return success

    def motor_flip(self) -> bool:
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        response = self._arduino_client.motor_flip()
        success = response and response.success
        if success:
            logger.info("Coin flipped successfully")
        else:
            logger.info("Failed to flip coin")
        return success

    def camera_trigger(self, duration: int | None = None) -> bool:
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        response = self._arduino_client.camera_trigger(duration)
        success = response and response.success
        if success:
            logger.info("Camera triggered successfully")
        else:
            logger.info("Failed to trigger camera")
        return success

    def emergency_stop(self) -> bool:
        if not self._arduino_client.is_connected:
            logger.warning("Not connected to ESP32")
            return False
        response = self._arduino_client.emergency_stop()
        success = response and response.success
        if success:
            logger.info("Emergency stop executed")
        else:
            logger.info("Failed to execute emergency stop")
        return success
    
    def add_status_callback(self, callback: Callable[[ConnectionStatus], None]) -> None:
        self._status_callbacks.add(callback)
    
    def add_response_callback(self, callback: Callable[[Response], None]) -> None:
        self._response_callbacks.add(callback)
    
    def add_event_callback(self, callback: Callable[[Message], None]) -> None:
        self._event_callbacks.add(callback)
    
    def add_heartbeat_callback(self, callback: Callable[[ConnectionHealth], None]) -> None:
        self._heartbeat_callbacks.add(callback)
    
    def add_ack_callback(self, callback: Callable[[AcknowledgmentInfo], None]) -> None:
        self._ack_callbacks.add(callback)
    
    def get_connection_health(self) -> ConnectionHealth:
        return self._arduino_client.get_connection_health()
    
    def _handle_response(self, response: Response) -> None:
        logger.debug(f"Handling async response: {response}")
        self._response_callbacks.notify(response)
    
    def _handle_event(self, event: Message) -> None:
        logger.info(f"Handling event: {event.type}")
        self._event_callbacks.notify(event)
    
    def _handle_heartbeat(self, health: ConnectionHealth) -> None:
        logger.debug(f"Heartbeat received - alive: {health.is_alive}, uptime: {health.esp32_uptime_ms}ms")
        self._heartbeat_callbacks.notify(health)
    
    def _handle_acknowledgment(self, ack: AcknowledgmentInfo) -> None:
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
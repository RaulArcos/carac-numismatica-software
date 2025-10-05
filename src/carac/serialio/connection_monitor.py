"""Connection monitoring for ESP32 heartbeat and timeout detection."""
import time
from typing import Callable
from threading import Thread, Lock
from dataclasses import dataclass, field

from loguru import logger

from ..config.settings import settings


@dataclass
class ConnectionHealth:
    """Connection health information."""
    is_alive: bool = False
    last_heartbeat_time: float = 0.0
    esp32_uptime_ms: int = 0
    seconds_since_heartbeat: float = 0.0
    heartbeat_count: int = 0


@dataclass
class AcknowledgmentInfo:
    """Information about a command acknowledgment."""
    received_type: str
    timestamp: int
    sent_time: float = field(default_factory=time.time)
    round_trip_ms: float = 0.0


class ConnectionMonitor:
    """Monitor ESP32 connection health via heartbeats and acknowledgments."""
    
    CHECK_INTERVAL_SECONDS = 1.0
    
    @property
    def heartbeat_timeout_seconds(self) -> float:
        """Get heartbeat timeout in seconds from settings."""
        return settings.heartbeat_timeout_ms / 1000.0
    
    @property
    def heartbeat_expected_interval_seconds(self) -> float:
        """Get expected heartbeat interval in seconds from settings."""
        return settings.heartbeat_interval_ms / 1000.0
    
    def __init__(self) -> None:
        self._lock = Lock()
        self._health = ConnectionHealth()
        self._monitoring = False
        self._monitor_thread: Thread | None = None
        
        # Track pending acknowledgments
        self._pending_acks: dict[str, float] = {}  # message_type -> sent_time
        self._last_ack: AcknowledgmentInfo | None = None
        
        # Callbacks
        self._heartbeat_callback: Callable[[ConnectionHealth], None] | None = None
        self._timeout_callback: Callable[[], None] | None = None
        self._ack_callback: Callable[[AcknowledgmentInfo], None] | None = None
    
    def start_monitoring(self) -> None:
        """Start connection monitoring."""
        if self._monitoring:
            logger.warning("Connection monitoring already active")
            return
        
        logger.info("Starting connection monitoring")
        self._monitoring = True
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop connection monitoring."""
        if not self._monitoring:
            return
        
        logger.info("Stopping connection monitoring")
        self._monitoring = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        with self._lock:
            self._health = ConnectionHealth()
            self._pending_acks.clear()
            self._last_ack = None
    
    def handle_heartbeat(self, uptime_ms: int, status: str) -> None:
        """Process a heartbeat message from ESP32."""
        current_time = time.time()
        
        with self._lock:
            previous_alive = self._health.is_alive
            
            self._health.is_alive = True
            self._health.last_heartbeat_time = current_time
            self._health.esp32_uptime_ms = uptime_ms
            self._health.seconds_since_heartbeat = 0.0
            self._health.heartbeat_count += 1
            
            health_snapshot = ConnectionHealth(
                is_alive=self._health.is_alive,
                last_heartbeat_time=self._health.last_heartbeat_time,
                esp32_uptime_ms=self._health.esp32_uptime_ms,
                seconds_since_heartbeat=self._health.seconds_since_heartbeat,
                heartbeat_count=self._health.heartbeat_count
            )
        
        if not previous_alive:
            logger.info("Connection restored - heartbeat received")
        
        logger.debug(
            f"Heartbeat #{health_snapshot.heartbeat_count}: "
            f"uptime={uptime_ms}ms, status={status}"
        )
        
        if self._heartbeat_callback:
            try:
                self._heartbeat_callback(health_snapshot)
            except Exception as e:
                logger.error(f"Error in heartbeat callback: {e}")
    
    def handle_acknowledgment(self, received_type: str, timestamp: int) -> None:
        """Process an acknowledgment message from ESP32."""
        current_time = time.time()
        
        with self._lock:
            sent_time = self._pending_acks.pop(received_type, current_time)
            round_trip_ms = (current_time - sent_time) * 1000
            
            ack_info = AcknowledgmentInfo(
                received_type=received_type,
                timestamp=timestamp,
                sent_time=sent_time,
                round_trip_ms=round_trip_ms
            )
            
            self._last_ack = ack_info
        
        logger.debug(f"✓ ACK for '{received_type}' (RTT: {round_trip_ms:.1f}ms)")
        
        if self._ack_callback:
            try:
                self._ack_callback(ack_info)
            except Exception as e:
                logger.error(f"Error in ACK callback: {e}")
    
    def register_command_sent(self, command_type: str) -> None:
        """Register that a command was sent (for RTT tracking)."""
        with self._lock:
            self._pending_acks[command_type] = time.time()
    
    def get_health(self) -> ConnectionHealth:
        """Get current connection health snapshot."""
        with self._lock:
            return ConnectionHealth(
                is_alive=self._health.is_alive,
                last_heartbeat_time=self._health.last_heartbeat_time,
                esp32_uptime_ms=self._health.esp32_uptime_ms,
                seconds_since_heartbeat=self._health.seconds_since_heartbeat,
                heartbeat_count=self._health.heartbeat_count
            )
    
    def get_last_acknowledgment(self) -> AcknowledgmentInfo | None:
        """Get the last received acknowledgment."""
        with self._lock:
            return self._last_ack
    
    def set_heartbeat_callback(self, callback: Callable[[ConnectionHealth], None]) -> None:
        """Set callback for heartbeat events."""
        self._heartbeat_callback = callback
    
    def set_timeout_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for connection timeout events."""
        self._timeout_callback = callback
    
    def set_ack_callback(self, callback: Callable[[AcknowledgmentInfo], None]) -> None:
        """Set callback for acknowledgment events."""
        self._ack_callback = callback
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop to detect timeouts."""
        while self._monitoring:
            current_time = time.time()
            
            with self._lock:
                if self._health.last_heartbeat_time > 0:
                    elapsed = current_time - self._health.last_heartbeat_time
                    self._health.seconds_since_heartbeat = elapsed
                    
                    # Check for timeout
                    if self._health.is_alive and elapsed > self.heartbeat_timeout_seconds:
                        self._health.is_alive = False
                        logger.warning(
                            f"Connection timeout detected "
                            f"(no heartbeat for {elapsed:.1f}s)"
                        )
                        
                        # Trigger timeout callback outside the lock
                        if self._timeout_callback:
                            try:
                                self._timeout_callback()
                            except Exception as e:
                                logger.error(f"Error in timeout callback: {e}")
            
            time.sleep(self.CHECK_INTERVAL_SECONDS)
    
    @property
    def is_alive(self) -> bool:
        """Check if connection is currently alive."""
        with self._lock:
            return self._health.is_alive


import time
from dataclasses import dataclass, field
from threading import Lock, Thread
from typing import Callable

from loguru import logger

from ..config.settings import settings


@dataclass
class ConnectionHealth:
    is_alive: bool = False
    last_heartbeat_time: float = 0.0
    esp32_uptime_ms: int = 0
    seconds_since_heartbeat: float = 0.0
    heartbeat_count: int = 0


@dataclass
class AcknowledgmentInfo:
    received_type: str
    timestamp: int
    sent_time: float = field(default_factory=time.time)
    round_trip_ms: float = 0.0


class ConnectionMonitor:
    CHECK_INTERVAL_SECONDS = 2.0
    THREAD_JOIN_TIMEOUT_SECONDS = 2.0

    @property
    def heartbeat_timeout_seconds(self) -> float:
        return settings.heartbeat_timeout_ms / 1000.0

    @property
    def heartbeat_expected_interval_seconds(self) -> float:
        return settings.heartbeat_interval_ms / 1000.0

    def __init__(self) -> None:
        self._lock = Lock()
        self._health = ConnectionHealth()
        self._monitoring = False
        self._monitor_thread: Thread | None = None
        self._pending_acks: dict[str, float] = {}
        self._last_ack: AcknowledgmentInfo | None = None
        self._heartbeat_callback: Callable[[ConnectionHealth], None] | None = None
        self._timeout_callback: Callable[[], None] | None = None
        self._ack_callback: Callable[[AcknowledgmentInfo], None] | None = None
    
    def start_monitoring(self) -> None:
        if self._monitoring:
            logger.warning("Connection monitoring already active")
            return
        logger.info("Starting connection monitoring")
        self._monitoring = True
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        if not self._monitoring:
            return
        logger.info("Stopping connection monitoring")
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=self.THREAD_JOIN_TIMEOUT_SECONDS)
        with self._lock:
            self._health = ConnectionHealth()
            self._pending_acks.clear()
            self._last_ack = None
    
    def handle_heartbeat(self, uptime_ms: int, status: str) -> None:
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
        
        if not self._heartbeat_callback:
            return

        try:
            self._heartbeat_callback(health_snapshot)
        except Exception as e:
            logger.error(f"Error in heartbeat callback: {e}")
    
    def handle_acknowledgment(self, received_type: str, timestamp: int) -> None:
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
        if not self._ack_callback:
            return

        try:
            self._ack_callback(ack_info)
        except Exception as e:
            logger.error(f"Error in ACK callback: {e}")
    
    def register_command_sent(self, command_type: str) -> None:
        with self._lock:
            self._pending_acks[command_type] = time.time()
    
    def get_health(self) -> ConnectionHealth:
        with self._lock:
            return ConnectionHealth(
                is_alive=self._health.is_alive,
                last_heartbeat_time=self._health.last_heartbeat_time,
                esp32_uptime_ms=self._health.esp32_uptime_ms,
                seconds_since_heartbeat=self._health.seconds_since_heartbeat,
                heartbeat_count=self._health.heartbeat_count
            )
    
    def get_last_acknowledgment(self) -> AcknowledgmentInfo | None:
        with self._lock:
            return self._last_ack
    
    def set_heartbeat_callback(self, callback: Callable[[ConnectionHealth], None]) -> None:
        self._heartbeat_callback = callback
    
    def set_timeout_callback(self, callback: Callable[[], None]) -> None:
        self._timeout_callback = callback
    
    def set_ack_callback(self, callback: Callable[[AcknowledgmentInfo], None]) -> None:
        self._ack_callback = callback
    
    def _monitor_loop(self) -> None:
        while self._monitoring:
            self._check_heartbeat_timeout(time.time())
            time.sleep(self.CHECK_INTERVAL_SECONDS)

    def _check_heartbeat_timeout(self, current_time: float) -> None:
        health_snapshot = None
        timeout_detected = False
        
        with self._lock:
            if self._health.last_heartbeat_time <= 0:
                return
            elapsed = current_time - self._health.last_heartbeat_time
            self._health.seconds_since_heartbeat = elapsed
            if self._health.is_alive and elapsed > self.heartbeat_timeout_seconds:
                self._health.is_alive = False
                timeout_detected = True
                logger.warning(f"Connection timeout detected (no heartbeat for {elapsed:.1f}s)")
                health_snapshot = ConnectionHealth(
                    is_alive=self._health.is_alive,
                    last_heartbeat_time=self._health.last_heartbeat_time,
                    esp32_uptime_ms=self._health.esp32_uptime_ms,
                    seconds_since_heartbeat=self._health.seconds_since_heartbeat,
                    heartbeat_count=self._health.heartbeat_count
                )
        
        if not timeout_detected or not health_snapshot:
            return

        if self._heartbeat_callback:
            try:
                self._heartbeat_callback(health_snapshot)
            except Exception as e:
                logger.error(f"Error in heartbeat callback: {e}")

        if self._timeout_callback:
            try:
                self._timeout_callback()
            except Exception as e:
                logger.error(f"Error in timeout callback: {e}")
    
    @property
    def is_alive(self) -> bool:
        with self._lock:
            return self._health.is_alive


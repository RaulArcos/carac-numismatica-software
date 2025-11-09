from loguru import logger
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ..config.settings import settings
from ..controllers.session_controller import SessionController
from ..protocol.models import ConnectionStatus, Message, MessageType, Response
from ..serialio.connection_monitor import AcknowledgmentInfo, ConnectionHealth
from .constants import (
    IconPaths,
    LayoutConstants,
    LightingConstants,
    SequenceConstants,
    ThrottleConstants,
    WindowConstants,
)
from .services import PortService, PresetService
from .services.port_service import PortRefreshThread
from .style_manager import style_manager
from .widgets import (
    ConnectionPanel,
    LightingControlPanel,
    LogPanel,
    PhotoControlPanel,
    PresetControlPanel,
    StatusCard,
    WeightDisplayWidget,
)


class MainWindow(QMainWindow):
    status_changed = Signal(object)
    response_received = Signal(object)
    event_received = Signal(object)
    heartbeat_received = Signal(object)
    weight_update = Signal(float)

    def __init__(self) -> None:
        super().__init__()
        self._session_controller = SessionController()
        self._port_refresh_timer = QTimer()
        self._port_refresh_thread = PortRefreshThread()
        self._sequence_timer = QTimer()
        self._sequence_step = 0
        self._sequence_running = False
        self._current_section_intensities: dict[str, int] = {
            "section1": 0,
            "section2": 0,
            "section3": 0,
            "section4": 0,
        }
        self._current_ring_intensities: dict[str, int] = {
            "ring_1": 0,
            "ring_2": 0,
            "ring_3": 0,
            "ring_4": 0,
        }
        self._weight_throttle_timer = QTimer()
        self._weight_throttle_timer.setSingleShot(True)
        self._pending_weight: float | None = None
        self._initialize_window()
        logger.info("Main window initialized")

    def _initialize_window(self) -> None:
        self._setup_window()
        self._setup_ui()
        self._setup_connections()
        self._setup_session_callbacks()
        self._start_port_refresh()
        self._apply_styles()

    def _setup_window(self) -> None:
        self.setWindowTitle(WindowConstants.TITLE)
        self.setGeometry(
            WindowConstants.X_POS,
            WindowConstants.Y_POS,
            WindowConstants.WIDTH,
            WindowConstants.HEIGHT,
        )
        self.setMinimumSize(WindowConstants.MIN_WIDTH, WindowConstants.MIN_HEIGHT)
        self._set_window_icon()

    def _set_window_icon(self) -> None:
        for icon_path in IconPaths.get_logo_paths():
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                logger.info(f"Application icon loaded from: {icon_path}")
                return
        logger.warning("Application icon not found")

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(
            LayoutConstants.MARGIN,
            LayoutConstants.MARGIN,
            LayoutConstants.MARGIN,
            LayoutConstants.MARGIN,
        )
        main_layout.setSpacing(LayoutConstants.SPACING)
        main_layout.addWidget(self._create_header())
        main_layout.addLayout(self._create_content_layout(), 1)

    def _create_header(self) -> QWidget:
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(LayoutConstants.HEADER_SPACING)
        header_layout.addLayout(self._create_title_section())
        header_layout.addStretch()
        header_layout.addLayout(self._create_status_cards())
        header_layout.addWidget(self._create_connection_panel())
        return header_widget

    def _create_title_section(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(LayoutConstants.TITLE_SECTION_SPACING)
        title_label = QLabel("CARAC - Control Numismático")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        subtitle_label = QLabel(WindowConstants.ORGANIZATION)
        subtitle_label.setObjectName("subtitleLabel")
        layout.addWidget(subtitle_label)
        return layout

    def _create_status_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(LayoutConstants.STATUS_CARD_SPACING)
        self._connection_card = StatusCard("Conexión", "Desconectado", "disconnected")
        layout.addWidget(self._connection_card)
        self._heartbeat_card = StatusCard("Heartbeat", "—", "inactive")
        layout.addWidget(self._heartbeat_card)
        self._arduino_card = StatusCard("Estado", "Sin datos", "inactive")
        layout.addWidget(self._arduino_card)
        return layout

    def _create_connection_panel(self) -> ConnectionPanel:
        self._connection_panel = ConnectionPanel()
        return self._connection_panel

    def _create_content_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(LayoutConstants.CONTENT_SPACING)
        layout.addWidget(self._create_left_panel(), 1.5)
        layout.addWidget(self._create_middle_panel(), 0.5)
        layout.addWidget(self._create_right_panel(), 1)
        return layout

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(LayoutConstants.PANEL_SPACING)
        self._lighting_panel = LightingControlPanel(settings.lighting_channels)
        layout.addWidget(self._lighting_panel)
        self._preset_panel = PresetControlPanel(PresetService.get_default_presets())
        layout.addWidget(self._preset_panel)
        return panel

    def _create_middle_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(LayoutConstants.PANEL_SPACING)
        self._photo_panel = PhotoControlPanel()
        layout.addWidget(self._photo_panel)
        self._weight_display = WeightDisplayWidget()
        layout.addWidget(self._weight_display)
        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(LayoutConstants.LOG_PANEL_SPACING)
        self._log_panel = LogPanel()
        layout.addWidget(self._log_panel)
        return panel

    def _setup_connections(self) -> None:
        self._connection_panel.port_refresh_requested.connect(self._refresh_ports)
        self._connection_panel.connection_toggle_requested.connect(self._toggle_connection)
        self._port_refresh_thread.ports_updated.connect(self._update_port_list)
        self._lighting_panel.section_changed.connect(self._on_section_changed)
        self._preset_panel.preset_selected.connect(self._on_preset_selected)
        self._photo_panel.position_forward_requested.connect(self._on_position_forward)
        self._photo_panel.position_backward_requested.connect(self._on_position_backward)
        self._photo_panel.flip_coin_requested.connect(self._on_flip_coin)
        self._photo_panel.take_photo_requested.connect(self._on_take_photo)
        self._photo_panel.start_sequence_requested.connect(self._on_start_sequence)
        self._photo_panel.stop_sequence_requested.connect(self._on_stop_sequence)
        self._photo_panel.emergency_stop_requested.connect(self._on_emergency_stop)
        self._photo_panel.led_toggle_requested.connect(self._on_toggle_led)
        self.status_changed.connect(self._on_connection_status_changed)
        self.response_received.connect(self._on_arduino_response)
        self.event_received.connect(self._on_esp32_event)
        self.heartbeat_received.connect(self._on_heartbeat_received)
        self.weight_update.connect(self._on_weight_update_throttled)
        self._weight_throttle_timer.timeout.connect(self._process_pending_weight)

    def _setup_session_callbacks(self) -> None:
        self._session_controller.add_status_callback(
            lambda s: self.status_changed.emit(s)
        )
        self._session_controller.add_response_callback(
            lambda r: self.response_received.emit(r)
        )
        self._session_controller.add_event_callback(
            lambda e: self.event_received.emit(e)
        )
        self._session_controller.add_heartbeat_callback(
            lambda h: self.heartbeat_received.emit(h)
        )
        self._session_controller.add_ack_callback(self._on_acknowledgment_received)

    def _start_port_refresh(self) -> None:
        self._port_refresh_timer.timeout.connect(self._refresh_ports)
        refresh_interval = settings.port_refresh_interval_ms
        self._port_refresh_timer.start(refresh_interval)
        logger.info(f"Port refresh started with interval: {refresh_interval}ms")
        self._refresh_ports()

    def _apply_styles(self) -> None:
        stylesheet = style_manager.get_combined_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
            logger.info("Applied combined stylesheet successfully")
        else:
            logger.warning("No stylesheet available")

    def _refresh_ports(self) -> None:
        if not self._port_refresh_thread.isRunning():
            self._port_refresh_thread.start()
        else:
            logger.debug("Port refresh skipped - previous refresh still in progress")

    def _update_port_list(self, ports: list[str]) -> None:
        annotated_ports = PortService.annotate_arduino_ports(ports)
        self._connection_panel.set_ports(annotated_ports)

    def _toggle_connection(self) -> None:
        if self._session_controller.is_connected:
            self._session_controller.disconnect()
        else:
            self._connect_to_arduino()

    def _connect_to_arduino(self) -> None:
        port = self._connection_panel.get_selected_port()
        if not port:
            QMessageBox.warning(self, "Error", "Por favor selecciona un puerto")
            return
        port = PortService.clean_port_name(port)
        self._log_panel.add_message(f"Conectando a {port}...")
        success = self._session_controller.connect(port, settings.default_baud_rate)
        self._log_panel.add_message(
            "Conectado exitosamente" if success else "Error de conexión",
            is_error=not success,
        )

    def _on_connection_status_changed(self, status: ConnectionStatus) -> None:
        if status == ConnectionStatus.CONNECTED:
            self._update_ui_connected()
        elif status == ConnectionStatus.CONNECTING:
            self._update_ui_connecting()
        elif status == ConnectionStatus.ERROR:
            self._update_ui_error()
        else:
            self._update_ui_disconnected()

    def _update_ui_connected(self) -> None:
        self._connection_panel.set_connect_button_text("Desconectar")
        self._connection_card.set_value("Conectado", "connected")
        self._photo_panel.set_system_info("Conectado", "connected")
        self._heartbeat_card.set_value("Esperando...", "connecting")
        style_manager.apply_button_style(
            self._connection_panel.connect_button, "disconnect"
        )

    def _update_ui_connecting(self) -> None:
        self._connection_card.set_value("Conectando...", "connecting")
        self._heartbeat_card.set_value("—", "inactive")

    def _update_ui_error(self) -> None:
        self._connection_card.set_value("Error", "disconnected")
        self._heartbeat_card.set_value("—", "inactive")

    def _update_ui_disconnected(self) -> None:
        self._connection_panel.set_connect_button_text("Conectar")
        self._connection_card.set_value("Desconectado", "disconnected")
        self._photo_panel.set_system_info("Desconectado", "disconnected")
        self._heartbeat_card.set_value("—", "inactive")
        self._connection_panel.connect_button.setObjectName("")
        style_manager.refresh_widget_style(self._connection_panel.connect_button)

    def _on_section_changed(self, section_index: int, intensity: int) -> None:
        self._preset_panel.clear_selection()
        if not self._session_controller.is_connected:
            return
        # Update only the corresponding ring (section_index maps to ring number)
        # Section 0 -> ring_1, Section 1 -> ring_2, etc.
        ring_channel = f"ring_{section_index + 1}"
        self._current_ring_intensities[ring_channel] = intensity
        success = self._send_all_ring_lighting()
        self._log_section_change(section_index, intensity, success)

    def _send_all_ring_lighting(self) -> bool:
        """Send all 4 ring lighting values in a single message."""
        try:
            sent = self._session_controller.set_sections_async(self._current_ring_intensities)
            if sent:
                logger.debug(f"Sent all ring lighting values: {self._current_ring_intensities}")
            else:
                logger.warning("Failed to send all ring lighting values")
            return sent
        except Exception as e:
            logger.error(f"Error sending all ring lighting values: {e}")
            return False

    def _log_section_change(self, section_index: int, intensity: int, success: bool) -> None:
        if success:
            normalized = intensity / LightingConstants.NORMALIZATION_FACTOR
            QTimer.singleShot(
                ThrottleConstants.LOG_DELAY_MS,
                lambda si=section_index, n=normalized: self._log_panel.add_message(
                    f"Anillo {si + 1} configurado a {n:.2f}"
                ),
            )
        else:
            QTimer.singleShot(
                ThrottleConstants.LOG_DELAY_MS,
                lambda si=section_index: self._log_panel.add_message(
                    f"Error al enviar comando Anillo {si + 1}",
                    is_error=True,
                ),
            )

    def _on_preset_selected(self, preset_name: str, preset_values: dict[str, int]) -> None:
        self._lighting_panel.set_all_values(preset_values)
        ring_intensities = self._calculate_ring_intensities(preset_values)
        if self._session_controller.is_connected:
            self._apply_preset_lighting(preset_name, ring_intensities)
        else:
            self._log_panel.add_message(f"Perfil '{preset_name}' aplicado (no conectado)")

    def _calculate_ring_intensities(
        self, preset_values: dict[str, int]
    ) -> dict[str, int]:
        ring_intensities: dict[str, int] = {}
        for ring_idx in range(1, 5):
            ring_key = f"ring_{ring_idx}"
            section_values = []
            for section_idx in range(1, 5):
                preset_key = f"ring{ring_idx}_section{section_idx}"
                if preset_key in preset_values:
                    section_values.append(preset_values[preset_key])
            if section_values:
                avg_intensity = sum(section_values) // len(section_values)
                ring_intensities[ring_key] = avg_intensity
        return ring_intensities

    def _apply_preset_lighting(
        self, preset_name: str, ring_intensities: dict[str, int]
    ) -> None:
        # Update current ring intensities
        self._current_ring_intensities.update(ring_intensities)
        # Send all ring values in one message
        sent = self._session_controller.set_sections_async(self._current_ring_intensities)
        if sent:
            self._log_panel.add_message(
                f"Perfil '{preset_name}' aplicado ({len(ring_intensities)} anillos configurados)"
            )
        else:
            self._log_panel.add_message(
                f"Perfil '{preset_name}' aplicado con errores",
                is_error=True,
            )

    def _on_position_forward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Moviendo moneda bajo la luz...")
        success = self._session_controller.motor_position("forward")
        self._log_panel.add_message(
            "Moneda posicionada bajo la luz" if success else "Error al mover moneda",
            is_error=not success,
        )

    def _on_position_backward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Retornando moneda...")
        success = self._session_controller.motor_position("backward")
        self._log_panel.add_message(
            "Moneda retornada" if success else "Error al retornar moneda",
            is_error=not success,
        )

    def _on_flip_coin(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Volteando moneda...")
        success = self._session_controller.motor_flip()
        self._log_panel.add_message(
            "Moneda volteada" if success else "Error al voltear moneda",
            is_error=not success,
        )

    def _on_take_photo(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Tomando fotografía...")
        success = self._session_controller.camera_trigger()
        self._log_panel.add_message(
            "Foto capturada" if success else "Error al tomar foto",
            is_error=not success,
        )

    def _on_start_sequence(self) -> None:
        if not self._check_connected():
            return
        if self._sequence_running:
            self._log_panel.add_message("Secuencia ya en ejecución", is_error=True)
            return
        self._log_panel.add_message("Iniciando secuencia completa...")
        self._photo_panel.set_sequence_active(True)
        self._arduino_card.set_value("En proceso", "progress")
        self._sequence_running = True
        self._sequence_step = 0
        self._sequence_timer.timeout.connect(self._execute_sequence_step)
        self._sequence_timer.setSingleShot(True)
        self._execute_sequence_step()

    def _execute_sequence_step(self) -> None:
        if not self._sequence_running:
            return
        if not self._session_controller.is_connected:
            self._handle_sequence_disconnection()
            return
        if self._sequence_step == 0:
            self._execute_first_flip()
        elif self._sequence_step == 1:
            self._execute_wait_and_second_flip()
        elif self._sequence_step == 2:
            self._execute_return()

    def _handle_sequence_disconnection(self) -> None:
        self._log_panel.add_message("Conexión perdida durante la secuencia", is_error=True)
        self._sequence_running = False
        self._photo_panel.set_sequence_active(False)
        self._sequence_step = 0
        self._disconnect_sequence_timer()

    def _execute_first_flip(self) -> None:
        self._log_panel.add_message("Paso 1/4: Volteando moneda (primera vez)...")
        success = self._session_controller.motor_flip()
        if success:
            self._sequence_step = 1
            self._sequence_timer.start(SequenceConstants.WAIT_DELAY_MS)
        else:
            self._handle_sequence_error("Error en el primer volteo")

    def _execute_wait_and_second_flip(self) -> None:
        self._log_panel.add_message("Paso 2/4: Espera completada (5s)")
        self._log_panel.add_message("Paso 3/4: Volteando moneda (segunda vez)...")
        success = self._session_controller.motor_flip()
        if success:
            self._sequence_step = 2
            self._sequence_timer.start(SequenceConstants.RETURN_DELAY_MS)
        else:
            self._handle_sequence_error("Error en el segundo volteo")

    def _execute_return(self) -> None:
        self._log_panel.add_message("Paso 4/4: Retornando moneda...")
        success = self._session_controller.motor_position("backward")
        if success:
            self._log_panel.add_message("✓ Secuencia completada exitosamente")
            self._arduino_card.set_value("Operativo", "operational")
        else:
            self._log_panel.add_message("Error al retornar moneda", is_error=True)
            self._arduino_card.set_value("Error", "disconnected")
        self._sequence_running = False
        self._photo_panel.set_sequence_active(False)
        self._sequence_step = 0
        self._disconnect_sequence_timer()

    def _handle_sequence_error(self, error_message: str) -> None:
        self._log_panel.add_message(error_message, is_error=True)
        self._sequence_running = False
        self._photo_panel.set_sequence_active(False)
        self._arduino_card.set_value("Error", "disconnected")
        self._disconnect_sequence_timer()

    def _disconnect_sequence_timer(self) -> None:
        try:
            self._sequence_timer.timeout.disconnect()
        except RuntimeError:
            pass

    def _on_stop_sequence(self) -> None:
        if not self._sequence_running:
            return
        self._log_panel.add_message("Deteniendo secuencia...", is_error=True)
        self._sequence_running = False
        self._sequence_step = 0
        self._sequence_timer.stop()
        self._disconnect_sequence_timer()
        self._photo_panel.set_sequence_active(False)
        self._arduino_card.set_value("Operativo", "operational")

    def _on_toggle_led(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Alternando LED de prueba...")
        response = self._session_controller.toggle_led()
        if response and response.success:
            led_state = (
                response.data.get("led_state", False) if response.data else False
            )
            self._photo_panel.set_led_status(led_state)
            state_text = "encendido" if led_state else "apagado"
            self._log_panel.add_message(f"LED de prueba {state_text}")
        else:
            self._log_panel.add_message("Error al alternar LED de prueba", is_error=True)

    def _on_emergency_stop(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("PARO DE EMERGENCIA ACTIVADO", is_error=True)
        success = self._session_controller.emergency_stop()
        if success:
            self._log_panel.add_message("Sistema detenido")
            self._photo_panel.set_sequence_active(False)
            self._arduino_card.set_value("Detenido", "disconnected")
        else:
            self._log_panel.add_message("Error en paro de emergencia", is_error=True)

    def _on_arduino_response(self, response: Response) -> None:
        if response.data and "led_state" in response.data:
            led_state = response.data["led_state"]
            self._photo_panel.set_led_status(led_state)
        if response.success:
            if not response.message or "lighting" not in response.message.lower():
                message = response.message
                if message:
                    self._log_panel.add_message(f"ESP32: {message}")
            self._arduino_card.set_value("Operativo", "operational")
        else:
            message = response.message
            self._log_panel.add_message(f"Error ESP32: {message}", is_error=True)
            self._arduino_card.set_value("Error", "disconnected")

    def _on_esp32_event(self, event: Message) -> None:
        logger.info(f"ESP32 Event: {event.type}")
        if event.type == MessageType.EVENT_STATUS:
            self._handle_status_event(event)
        elif event.type == MessageType.EVENT_SEQUENCE_STARTED:
            self._handle_sequence_started_event(event)
        elif event.type == MessageType.EVENT_SEQUENCE_PROGRESS:
            self._handle_sequence_progress_event(event)
        elif event.type == MessageType.EVENT_SEQUENCE_COMPLETED:
            self._handle_sequence_completed_event(event)
        elif event.type == MessageType.EVENT_SEQUENCE_STOPPED:
            self._handle_sequence_stopped_event(event)
        elif event.type == MessageType.EVENT_ERROR:
            self._handle_error_event(event)
        elif event.type == MessageType.EVENT_CAMERA_TRIGGERED:
            self._handle_camera_triggered_event(event)
        elif event.type == MessageType.EVENT_MOTOR_COMPLETE:
            self._handle_motor_complete_event(event)
        elif event.type == MessageType.EVENT_WEIGHT_READING:
            self._handle_weight_reading_event(event)

    def _handle_status_event(self, event: Message) -> None:
        message = event.payload.get("message", "Ready")
        firmware_version = event.payload.get("firmware_version", "Unknown")
        self._log_panel.add_message(f"{message} (Firmware: v{firmware_version})")
        self._arduino_card.set_value(f"{message}", "Ready")

    def _handle_sequence_started_event(self, event: Message) -> None:
        total = event.payload.get("total_photos", 0)
        self._log_panel.add_message(f"Secuencia iniciada: {total} fotos")
        self._photo_panel.set_sequence_active(True)

    def _handle_sequence_progress_event(self, event: Message) -> None:
        current = event.payload.get("current_photo", 0)
        total = event.payload.get("total_photos", 0)
        action = event.payload.get("action", "")
        self._log_panel.add_message(f"Progreso: {current}/{total} - {action}")

    def _handle_sequence_completed_event(self, event: Message) -> None:
        photos = event.payload.get("photos_taken", 0)
        duration = event.payload.get("duration", 0)
        self._log_panel.add_message(
            f"Secuencia completada: {photos} fotos en {duration:.1f}s"
        )
        self._photo_panel.set_sequence_active(False)

    def _handle_sequence_stopped_event(self, event: Message) -> None:
        reason = event.payload.get("reason", "unknown")
        photos = event.payload.get("photos_taken", 0)
        self._log_panel.add_message(
            f"Secuencia detenida ({reason}): {photos} fotos", is_error=True
        )
        self._photo_panel.set_sequence_active(False)

    def _handle_error_event(self, event: Message) -> None:
        msg = event.payload.get("message", "Error desconocido")
        severity = event.payload.get("severity", "medium")
        self._log_panel.add_message(f"Error [{severity}]: {msg}", is_error=True)

    def _handle_camera_triggered_event(self, event: Message) -> None:
        duration = event.payload.get("duration", 0)
        self._log_panel.add_message(f"Cámara activada ({duration}ms)")

    def _handle_motor_complete_event(self, event: Message) -> None:
        position = event.payload.get("position", 0)
        self._log_panel.add_message(f"Motor en posición: {position}")

    def _handle_weight_reading_event(self, event: Message) -> None:
        weight = event.payload.get("weight", 0.0)
        self.weight_update.emit(weight)

    def _on_heartbeat_received(self, health: ConnectionHealth) -> None:
        if health.is_alive:
            self._heartbeat_card.set_value("Active", "connected")
            if health.heartbeat_count % 10 == 0:
                uptime_seconds = health.esp32_uptime_ms / 1000
                if uptime_seconds < 60:
                    uptime_str = f"{uptime_seconds:.0f}s"
                elif uptime_seconds < 3600:
                    uptime_str = f"{uptime_seconds / 60:.1f}m"
                else:
                    uptime_str = f"{uptime_seconds / 3600:.1f}h"
                logger.debug(f"Heartbeat #{health.heartbeat_count}: uptime={uptime_str}")
        else:
            self._heartbeat_card.set_value("dead", "disconnected")
            self._log_panel.add_message(
                "⚠ Conexión perdida - sin heartbeat", is_error=True
            )
            logger.warning("Heartbeat timeout - connection lost")

    def _on_acknowledgment_received(self, ack: AcknowledgmentInfo) -> None:
        logger.debug(
            f"✓ Command '{ack.received_type}' acknowledged (RTT: {ack.round_trip_ms:.1f}ms)"
        )

    def _on_weight_update_throttled(self, weight: float) -> None:
        self._pending_weight = weight
        if not self._weight_throttle_timer.isActive():
            self._process_pending_weight()
            self._weight_throttle_timer.start(ThrottleConstants.WEIGHT_UPDATE_MS)

    def _process_pending_weight(self) -> None:
        if self._pending_weight is not None:
            self._weight_display.set_weight(self._pending_weight)
            self._pending_weight = None

    def _check_connected(self) -> bool:
        if not self._session_controller.is_connected:
            QMessageBox.warning(self, "Error", "No conectado a Arduino")
            return False
        return True

    def closeEvent(self, event) -> None:
        if self._sequence_running:
            self._sequence_timer.stop()
            self._disconnect_sequence_timer()
        if self._session_controller.is_connected:
            self._session_controller.disconnect()
        self._port_refresh_timer.stop()
        if self._port_refresh_thread.isRunning():
            self._port_refresh_thread.quit()
            self._port_refresh_thread.wait()
        event.accept()

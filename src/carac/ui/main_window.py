from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt, QTimer
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
    WINDOW_TITLE = "CARAC - Control Numismático UCA"
    WINDOW_ORGANIZATION = "Universidad de Cádiz"
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 650
    WINDOW_X = 100
    WINDOW_Y = 100
    MIN_WIDTH = 900
    MIN_HEIGHT = 580
    LAYOUT_MARGIN = 8
    LAYOUT_SPACING = 8
    HEADER_SPACING = 12
    STATUS_CARD_SPACING = 6
    TITLE_SECTION_SPACING = 5
    CONTENT_SPACING = 8
    PANEL_SPACING = 5
    LOG_PANEL_SPACING = 6
    SEQUENCE_STEP_COUNT = 4
    SEQUENCE_WAIT_DELAY_MS = 5000
    SEQUENCE_RETURN_DELAY_MS = 1000
    LOG_THROTTLE_DELAY_MS = 50
    NORMALIZATION_FACTOR = 255.0

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
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setGeometry(self.WINDOW_X, self.WINDOW_Y, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        
        icon_paths = [
            Path(__file__).parent.parent.parent / "assets" / "ui" / "logo.png",
            Path.cwd() / "assets" / "ui" / "logo.png",
        ]
        for icon_path in icon_paths:
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                logger.info(f"Application icon loaded from: {icon_path}")
                return
        logger.warning("Application icon not found")
    
    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(self.LAYOUT_MARGIN, self.LAYOUT_MARGIN, self.LAYOUT_MARGIN, self.LAYOUT_MARGIN)
        main_layout.setSpacing(self.LAYOUT_SPACING)
        main_layout.addWidget(self._create_header())
        main_layout.addLayout(self._create_content_layout(), 1)
    
    def _create_header(self) -> QWidget:
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(self.HEADER_SPACING)
        
        header_layout.addLayout(self._create_title_section())
        header_layout.addStretch()
        header_layout.addLayout(self._create_status_cards())
        header_layout.addWidget(self._create_connection_panel())
        
        return header_widget
    
    def _create_title_section(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(self.TITLE_SECTION_SPACING)
        
        title_label = QLabel("CARAC - Control Numismático")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel(self.WINDOW_ORGANIZATION)
        subtitle_label.setObjectName("subtitleLabel")
        layout.addWidget(subtitle_label)
        
        return layout
    
    def _create_status_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(self.STATUS_CARD_SPACING)
        
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
        layout.setSpacing(self.CONTENT_SPACING)
        
        layout.addWidget(self._create_left_panel(), 1.5)
        layout.addWidget(self._create_middle_panel(), 0.5)
        layout.addWidget(self._create_right_panel(), 1)
        
        return layout
    
    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.PANEL_SPACING)
        
        self._lighting_panel = LightingControlPanel(settings.lighting_channels)
        layout.addWidget(self._lighting_panel)
        
        self._preset_panel = PresetControlPanel(PresetService.get_default_presets())
        layout.addWidget(self._preset_panel)
        
        return panel
    
    def _create_middle_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.PANEL_SPACING)
        
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
        layout.setSpacing(self.LOG_PANEL_SPACING)
        
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
    
    def _setup_session_callbacks(self) -> None:
        self._session_controller.add_status_callback(self._on_connection_status_changed)
        self._session_controller.add_response_callback(self._on_arduino_response)
        self._session_controller.add_event_callback(self._on_esp32_event)
        self._session_controller.add_heartbeat_callback(self._on_heartbeat_received)
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
        self._log_panel.add_message("Conectado exitosamente" if success else "Error de conexión", is_error=not success)
    
    def _on_connection_status_changed(self, status: ConnectionStatus) -> None:
        if status == ConnectionStatus.CONNECTED:
            QTimer.singleShot(0, lambda: self._connection_panel.set_connect_button_text("Desconectar"))
            QTimer.singleShot(0, lambda: self._connection_card.set_value("Conectado", "connected"))
            QTimer.singleShot(0, lambda: self._photo_panel.set_system_info("Conectado", "connected"))
            QTimer.singleShot(0, lambda: self._heartbeat_card.set_value("Esperando...", "connecting"))
            QTimer.singleShot(0, lambda: style_manager.apply_button_style(
                self._connection_panel.connect_button, "disconnect"
            ))
        elif status == ConnectionStatus.CONNECTING:
            QTimer.singleShot(0, lambda: self._connection_card.set_value("Conectando...", "connecting"))
            QTimer.singleShot(0, lambda: self._heartbeat_card.set_value("—", "inactive"))
        elif status == ConnectionStatus.ERROR:
            QTimer.singleShot(0, lambda: self._connection_card.set_value("Error", "disconnected"))
            QTimer.singleShot(0, lambda: self._heartbeat_card.set_value("—", "inactive"))
        else:
            QTimer.singleShot(0, lambda: self._connection_panel.set_connect_button_text("Conectar"))
            QTimer.singleShot(0, lambda: self._connection_card.set_value("Desconectado", "disconnected"))
            QTimer.singleShot(0, lambda: self._photo_panel.set_system_info("Desconectado", "disconnected"))
            QTimer.singleShot(0, lambda: self._heartbeat_card.set_value("—", "inactive"))
            QTimer.singleShot(0, lambda: (
                self._connection_panel.connect_button.setObjectName(""),
                style_manager.refresh_widget_style(self._connection_panel.connect_button)
            ))
    
    def _on_section_changed(self, section_index: int, intensity: int) -> None:
        self._preset_panel.clear_selection()
        
        if not self._session_controller.is_connected:
            return
        
        success_count = 0
        for ring_idx in range(1, 5):
            ring_channel = f"ring_{ring_idx}"
            try:
                success = self._session_controller.set_lighting(ring_channel, intensity)
                if success:
                    success_count += 1
            except Exception as e:
                logger.error(f"Error setting lighting for {ring_channel}: {e}")
        
        if success_count == 4:
            normalized = intensity / self.NORMALIZATION_FACTOR
            QTimer.singleShot(self.LOG_THROTTLE_DELAY_MS, lambda si=section_index, n=normalized: self._log_panel.add_message(
                f"Sección {si + 1} configurada a {n:.2f} (todos los anillos)"
            ))
        elif success_count < 4:
            QTimer.singleShot(self.LOG_THROTTLE_DELAY_MS, lambda si=section_index, sc=success_count: self._log_panel.add_message(
                f"Error al configurar Sección {si + 1} ({sc}/4 anillos)",
                is_error=True
            ))
    
    def _on_preset_selected(self, preset_name: str, preset_values: dict[str, int]) -> None:
        self._lighting_panel.set_all_values(preset_values)
        
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
        
        if self._session_controller.is_connected:
            success_count = 0
            for ring_channel, intensity in ring_intensities.items():
                success = self._session_controller.set_lighting(ring_channel, intensity)
                if success:
                    success_count += 1
            
            if success_count == len(ring_intensities):
                self._log_panel.add_message(f"Perfil '{preset_name}' aplicado ({len(ring_intensities)} anillos configurados)")
            else:
                self._log_panel.add_message(
                    f"Perfil '{preset_name}' aplicado con errores ({success_count}/{len(ring_intensities)} anillos)",
                    is_error=True
                )
        else:
            self._log_panel.add_message(f"Perfil '{preset_name}' aplicado (no conectado)")
    
    def _on_position_forward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Moviendo moneda bajo la luz...")
        success = self._session_controller.motor_position("forward")
        self._log_panel.add_message("Moneda posicionada bajo la luz" if success else "Error al mover moneda", is_error=not success)
    
    def _on_position_backward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Retornando moneda...")
        success = self._session_controller.motor_position("backward")
        self._log_panel.add_message("Moneda retornada" if success else "Error al retornar moneda", is_error=not success)
    
    def _on_flip_coin(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Volteando moneda...")
        success = self._session_controller.motor_flip()
        self._log_panel.add_message("Moneda volteada" if success else "Error al voltear moneda", is_error=not success)
    
    def _on_take_photo(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Tomando fotografía...")
        success = self._session_controller.camera_trigger()
        self._log_panel.add_message("Foto capturada" if success else "Error al tomar foto", is_error=not success)
    
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
            self._log_panel.add_message("Conexión perdida durante la secuencia", is_error=True)
            self._sequence_running = False
            self._photo_panel.set_sequence_active(False)
            self._sequence_step = 0
            self._disconnect_sequence_timer()
            return
        
        if self._sequence_step == 0:
            self._log_panel.add_message("Paso 1/4: Volteando moneda (primera vez)...")
            success = self._session_controller.motor_flip()
            if success:
                self._sequence_step = 1
                self._sequence_timer.start(self.SEQUENCE_WAIT_DELAY_MS)
            else:
                self._handle_sequence_error("Error en el primer volteo")
        elif self._sequence_step == 1:
            self._log_panel.add_message("Paso 2/4: Espera completada (5s)")
            self._log_panel.add_message("Paso 3/4: Volteando moneda (segunda vez)...")
            success = self._session_controller.motor_flip()
            if success:
                self._sequence_step = 2
                self._sequence_timer.start(self.SEQUENCE_RETURN_DELAY_MS)
            else:
                self._handle_sequence_error("Error en el segundo volteo")
        elif self._sequence_step == 2:
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
            led_state = response.data.get('led_state', False) if response.data else False
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
        if response.data and 'led_state' in response.data:
            led_state = response.data['led_state']
            QTimer.singleShot(0, lambda ls=led_state: self._photo_panel.set_led_status(ls))
        
        if response.success:
            message = response.message
            QTimer.singleShot(0, lambda m=message: self._log_panel.add_message(f"ESP32: {m}"))
            QTimer.singleShot(0, lambda: self._arduino_card.set_value("Operativo", "operational"))
        else:
            message = response.message
            QTimer.singleShot(0, lambda m=message: self._log_panel.add_message(
                f"Error ESP32: {m}", is_error=True
            ))
            QTimer.singleShot(0, lambda: self._arduino_card.set_value("Error", "disconnected"))
    
    def _on_esp32_event(self, event: Message) -> None:
        logger.info(f"ESP32 Event: {event.type}")
        
        if event.type == MessageType.EVENT_STATUS:
            message = event.payload.get("message", "Ready")
            firmware_version = event.payload.get("firmware_version", "Unknown")
            QTimer.singleShot(0, lambda m=message, fv=firmware_version: self._log_panel.add_message(
                f"{m} (Firmware: v{fv})"
            ))
            QTimer.singleShot(0, lambda m=message: self._arduino_card.set_value(f"{m}", "Ready"))
        
        elif event.type == MessageType.EVENT_SEQUENCE_STARTED:
            total = event.payload.get("total_photos", 0)
            QTimer.singleShot(0, lambda t=total: self._log_panel.add_message(f"Secuencia iniciada: {t} fotos"))
            QTimer.singleShot(0, lambda: self._photo_panel.set_sequence_active(True))
        
        elif event.type == MessageType.EVENT_SEQUENCE_PROGRESS:
            current = event.payload.get("current_photo", 0)
            total = event.payload.get("total_photos", 0)
            action = event.payload.get("action", "")
            QTimer.singleShot(0, lambda c=current, t=total, a=action: self._log_panel.add_message(f"Progreso: {c}/{t} - {a}"))
        
        elif event.type == MessageType.EVENT_SEQUENCE_COMPLETED:
            photos = event.payload.get("photos_taken", 0)
            duration = event.payload.get("duration", 0)
            QTimer.singleShot(0, lambda p=photos, d=duration: self._log_panel.add_message(
                f"Secuencia completada: {p} fotos en {d:.1f}s"
            ))
            QTimer.singleShot(0, lambda: self._photo_panel.set_sequence_active(False))
        
        elif event.type == MessageType.EVENT_SEQUENCE_STOPPED:
            reason = event.payload.get("reason", "unknown")
            photos = event.payload.get("photos_taken", 0)
            QTimer.singleShot(0, lambda r=reason, p=photos: self._log_panel.add_message(
                f"Secuencia detenida ({r}): {p} fotos", is_error=True
            ))
            QTimer.singleShot(0, lambda: self._photo_panel.set_sequence_active(False))
        
        elif event.type == MessageType.EVENT_ERROR:
            msg = event.payload.get("message", "Error desconocido")
            severity = event.payload.get("severity", "medium")
            QTimer.singleShot(0, lambda m=msg, s=severity: self._log_panel.add_message(
                f"Error [{s}]: {m}", is_error=True
            ))
        
        elif event.type == MessageType.EVENT_CAMERA_TRIGGERED:
            duration = event.payload.get("duration", 0)
            QTimer.singleShot(0, lambda d=duration: self._log_panel.add_message(f"Cámara activada ({d}ms)"))
        
        elif event.type == MessageType.EVENT_MOTOR_COMPLETE:
            position = event.payload.get("position", 0)
            QTimer.singleShot(0, lambda p=position: self._log_panel.add_message(f"Motor en posición: {p}"))
        
        elif event.type == MessageType.EVENT_WEIGHT_READING:
            weight = event.payload.get("weight", 0.0)
            QTimer.singleShot(0, lambda w=weight: self._weight_display.set_weight(w))
    
    def _on_heartbeat_received(self, health: ConnectionHealth) -> None:
        if health.is_alive:
            QTimer.singleShot(0, lambda: self._heartbeat_card.set_value("Active", "connected"))
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
            QTimer.singleShot(0, lambda: self._heartbeat_card.set_value("dead", "disconnected"))
            QTimer.singleShot(0, lambda: self._log_panel.add_message(
                "⚠ Conexión perdida - sin heartbeat", is_error=True
            ))
            logger.warning("Heartbeat timeout - connection lost")
    
    def _on_acknowledgment_received(self, ack: AcknowledgmentInfo) -> None:
        logger.debug(f"✓ Command '{ack.received_type}' acknowledged (RTT: {ack.round_trip_ms:.1f}ms)")
    
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
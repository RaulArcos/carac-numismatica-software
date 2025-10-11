from pathlib import Path

from loguru import logger
from PySide6.QtCore import QTimer
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
from ..protocol.models import ConnectionStatus, Message, Response
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
)


class MainWindow(QMainWindow):
    WINDOW_TITLE = "CARAC - Control Numismático UCA"
    WINDOW_ORGANIZATION = "Universidad de Cádiz"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 750
    WINDOW_X = 100
    WINDOW_Y = 100
    MIN_WIDTH = 1100
    MIN_HEIGHT = 700
    PORT_REFRESH_INTERVAL_MS = 5000
    LAYOUT_MARGIN = 10
    LAYOUT_SPACING = 10
    HEADER_SPACING = 15
    STATUS_CARD_SPACING = 8

    def __init__(self) -> None:
        super().__init__()

        self._session_controller = SessionController()
        self._port_refresh_timer = QTimer()
        self._port_refresh_thread = PortRefreshThread()
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
        self.setGeometry(
            self.WINDOW_X,
            self.WINDOW_Y,
            self.WINDOW_WIDTH,
            self.WINDOW_HEIGHT
        )
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self._load_window_icon()
    
    def _load_window_icon(self) -> None:
        icon_paths = [
            Path(__file__).parent.parent.parent / "assets" / "ui" / "logo.png",
            Path.cwd() / "assets" / "ui" / "logo.png",
        ]

        for icon_path in icon_paths:
            if self._try_load_icon(icon_path):
                return

        logger.warning("Application icon not found")

    def _try_load_icon(self, icon_path: Path) -> bool:
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            logger.info(f"Application icon loaded from: {icon_path}")
            return True
        return False
    
    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN
        )
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
        layout.setSpacing(5)
        
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
        layout.setSpacing(10)
        
        layout.addWidget(self._create_left_panel(), 1.5)
        layout.addWidget(self._create_middle_panel(), 0.5)
        layout.addWidget(self._create_right_panel(), 1)
        
        return layout
    
    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self._lighting_panel = LightingControlPanel(settings.lighting_channels)
        layout.addWidget(self._lighting_panel)
        
        self._preset_panel = PresetControlPanel(PresetService.get_default_presets())
        layout.addWidget(self._preset_panel)
        
        return panel
    
    def _create_middle_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self._photo_panel = PhotoControlPanel()
        layout.addWidget(self._photo_panel)
        layout.addStretch()
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
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
        self._port_refresh_timer.start(self.PORT_REFRESH_INTERVAL_MS)
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
        self._log_connection_result(success)

    def _log_connection_result(self, success: bool) -> None:
        if success:
            self._log_panel.add_message("Conectado exitosamente")
        else:
            self._log_panel.add_message("Error de conexión", is_error=True)
    
    def _on_connection_status_changed(self, status: ConnectionStatus) -> None:
        if status == ConnectionStatus.CONNECTED:
            self._connection_panel.set_connect_button_text("Desconectar")
            style_manager.apply_button_style(self._connection_panel.connect_button, "disconnect")
            self._connection_card.set_value("Conectado", "connected")
            self._photo_panel.set_system_info("Conectado", "connected")
            self._heartbeat_card.set_value("Esperando...", "connecting")
        elif status == ConnectionStatus.CONNECTING:
            self._connection_card.set_value("Conectando...", "connecting")
            self._heartbeat_card.set_value("—", "inactive")
        elif status == ConnectionStatus.ERROR:
            self._connection_card.set_value("Error", "disconnected")
            self._heartbeat_card.set_value("—", "inactive")
        else:
            self._connection_panel.set_connect_button_text("Conectar")
            self._connection_panel.connect_button.setObjectName("")
            style_manager.refresh_widget_style(self._connection_panel.connect_button)
            self._connection_card.set_value("Desconectado", "disconnected")
            self._photo_panel.set_system_info("Desconectado", "disconnected")
            self._heartbeat_card.set_value("—", "inactive")
    
    def _on_section_changed(self, section_index: int, intensity: int) -> None:
        """Called when a section slider is moved - sends all sections to ESP32"""
        self._preset_panel.clear_selection()
        
        # Update the changed section in our state
        section_key = f"section{section_index + 1}"
        self._current_section_intensities[section_key] = intensity
        
        if self._session_controller.is_connected:
            # Send all sections at once
            success = self._session_controller.set_sections(self._current_section_intensities)
            
            if success:
                normalized = intensity / 255.0
                self._log_panel.add_message(f"Sección {section_index + 1} configurada a {normalized:.2f}")
            else:
                self._log_panel.add_message(f"Error al configurar Sección {section_index + 1}", is_error=True)
    
    def _on_preset_selected(self, preset_name: str, preset_values: dict[str, int]) -> None:
        self._lighting_panel.set_all_values(preset_values)
        
        # Extract section intensities from ring1 (all rings have same values per section)
        sections_to_send = {}
        for section_idx in range(1, 5):
            channel = f"ring1_section{section_idx}"
            if channel in preset_values:
                intensity = preset_values[channel]
                section_key = f"section{section_idx}"
                sections_to_send[section_key] = intensity
                # Update internal state
                self._current_section_intensities[section_key] = intensity
        
        # Send all sections in one command if connected
        if self._session_controller.is_connected:
            success = self._session_controller.set_sections(sections_to_send)
            
            if success:
                self._log_panel.add_message(f"Perfil '{preset_name}' aplicado (4 secciones configuradas)")
            else:
                self._log_panel.add_message(
                    f"Perfil '{preset_name}' aplicado con errores",
                    is_error=True
                )
        else:
            self._log_panel.add_message(f"Perfil '{preset_name}' aplicado (no conectado)")
    
    def _on_position_forward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Moviendo posición hacia adelante...")
        success = self._session_controller.motor_position("forward")
        if success:
            self._log_panel.add_message("Posición adelantada")
        else:
            self._log_panel.add_message("Error al mover posición", is_error=True)
    
    def _on_position_backward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Moviendo posición hacia atrás...")
        success = self._session_controller.motor_position("backward")
        if success:
            self._log_panel.add_message("Posición retrocedida")
        else:
            self._log_panel.add_message("Error al mover posición", is_error=True)
    
    def _on_flip_coin(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Volteando moneda...")
        success = self._session_controller.motor_flip()
        if success:
            self._log_panel.add_message("Moneda volteada")
        else:
            self._log_panel.add_message("Error al voltear moneda", is_error=True)
    
    def _on_take_photo(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Tomando fotografía...")
        success = self._session_controller.camera_trigger()
        if success:
            self._log_panel.add_message("Foto capturada")
        else:
            self._log_panel.add_message("Error al tomar foto", is_error=True)
    
    def _on_start_sequence(self) -> None:
        if not self._check_connected():
            return
        
        self._log_panel.add_message("Iniciando secuencia completa...")
        self._photo_panel.set_sequence_active(True)
        self._arduino_card.set_value("En proceso", "progress")
    
    def _on_stop_sequence(self) -> None:
        self._log_panel.add_message("Deteniendo secuencia...", is_error=True)
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
            self._photo_panel.set_led_status(led_state)
        
        if response.success:
            self._log_panel.add_message(f"ESP32: {response.message}")
            self._arduino_card.set_value("Operativo", "operational")
        else:
            self._log_panel.add_message(f"Error ESP32: {response.message}", is_error=True)
            self._arduino_card.set_value("Error", "disconnected")
    
    def _on_esp32_event(self, event) -> None:
        from ..protocol.models import Message, MessageType
        
        if not isinstance(event, Message):
            return
        
        logger.info(f"ESP32 Event: {event.type}")
        
        if event.type == MessageType.EVENT_STATUS:
            message = event.payload.get("message", "Ready")
            firmware_version = event.payload.get("firmware_version", "Unknown")
            self._log_panel.add_message(f"{message} (Firmware: v{firmware_version})")
            self._arduino_card.set_value(f"{message}", "Ready")
        
        elif event.type == MessageType.EVENT_SEQUENCE_STARTED:
            total = event.payload.get("total_photos", 0)
            self._log_panel.add_message(f"Secuencia iniciada: {total} fotos")
            self._photo_panel.set_sequence_active(True)
        
        elif event.type == MessageType.EVENT_SEQUENCE_PROGRESS:
            current = event.payload.get("current_photo", 0)
            total = event.payload.get("total_photos", 0)
            action = event.payload.get("action", "")
            self._log_panel.add_message(f"Progreso: {current}/{total} - {action}")
        
        elif event.type == MessageType.EVENT_SEQUENCE_COMPLETED:
            photos = event.payload.get("photos_taken", 0)
            duration = event.payload.get("duration", 0)
            self._log_panel.add_message(f"Secuencia completada: {photos} fotos en {duration:.1f}s")
            self._photo_panel.set_sequence_active(False)
        
        elif event.type == MessageType.EVENT_SEQUENCE_STOPPED:
            reason = event.payload.get("reason", "unknown")
            photos = event.payload.get("photos_taken", 0)
            self._log_panel.add_message(f"Secuencia detenida ({reason}): {photos} fotos", is_error=True)
            self._photo_panel.set_sequence_active(False)
        
        elif event.type == MessageType.EVENT_ERROR:
            msg = event.payload.get("message", "Error desconocido")
            severity = event.payload.get("severity", "medium")
            self._log_panel.add_message(f"Error [{severity}]: {msg}", is_error=True)
        
        elif event.type == MessageType.EVENT_CAMERA_TRIGGERED:
            duration = event.payload.get("duration", 0)
            self._log_panel.add_message(f"Cámara activada ({duration}ms)")
        
        elif event.type == MessageType.EVENT_MOTOR_COMPLETE:
            position = event.payload.get("position", 0)
            self._log_panel.add_message(f"Motor en posición: {position}")
    
    def _on_heartbeat_received(self, health: ConnectionHealth) -> None:
        if health.is_alive:
            self._handle_alive_heartbeat(health)
        else:
            self._handle_lost_heartbeat()

    def _handle_alive_heartbeat(self, health: ConnectionHealth) -> None:
        self._heartbeat_card.set_value("Active", "connected")

        if health.heartbeat_count % 10 == 0:
            uptime_str = self._format_uptime(health.esp32_uptime_ms)
            logger.debug(f"Heartbeat #{health.heartbeat_count}: uptime={uptime_str}")

    def _handle_lost_heartbeat(self) -> None:
        self._heartbeat_card.set_value("dead", "disconnected")
        self._log_panel.add_message(
            "⚠ Conexión perdida - sin heartbeat",
            is_error=True
        )
        logger.warning("Heartbeat timeout - connection lost")

    def _format_uptime(self, uptime_ms: int) -> str:
        uptime_seconds = uptime_ms / 1000

        if uptime_seconds < 60:
            return f"{uptime_seconds:.0f}s"
        elif uptime_seconds < 3600:
            minutes = uptime_seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = uptime_seconds / 3600
            return f"{hours:.1f}h"
    
    def _on_acknowledgment_received(self, ack: AcknowledgmentInfo) -> None:
        logger.debug(
            f"✓ Command '{ack.received_type}' acknowledged "
            f"(RTT: {ack.round_trip_ms:.1f}ms)"
        )
    
    def _check_connected(self) -> bool:
        if not self._session_controller.is_connected:
            QMessageBox.warning(self, "Error", "No conectado a Arduino")
            return False
        return True
    
    def closeEvent(self, event) -> None:
        self._cleanup()
        event.accept()

    def _cleanup(self) -> None:
        if self._session_controller.is_connected:
            self._session_controller.disconnect()

        self._stop_port_refresh()

    def _stop_port_refresh(self) -> None:
        self._port_refresh_timer.stop()
        if self._port_refresh_thread.isRunning():
            self._port_refresh_thread.quit()
            self._port_refresh_thread.wait()
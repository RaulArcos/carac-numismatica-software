from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

from loguru import logger

from ..config.settings import settings
from ..controllers.session_controller import SessionController
from ..protocol.models import ConnectionStatus, Response
from .style_manager import style_manager
from .widgets import (
    StatusCard,
    ConnectionPanel,
    LightingControlPanel,
    PresetControlPanel,
    PhotoControlPanel,
    LogPanel,
)
from .services import PresetService, PortService
from .services.port_service import PortRefreshThread


class MainWindow(QMainWindow):
    WINDOW_TITLE = "CARAC - Control Numismático UCA"
    WINDOW_ORGANIZATION = "Universidad de Cádiz"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 750
    MIN_WIDTH = 1100
    MIN_HEIGHT = 700
    PORT_REFRESH_INTERVAL = 5000
    
    def __init__(self) -> None:
        super().__init__()
        
        self._session_controller = SessionController()
        self._port_refresh_timer = QTimer()
        self._port_refresh_thread = PortRefreshThread()
        
        self._setup_window()
        self._setup_ui()
        self._setup_connections()
        self._setup_session_callbacks()
        self._start_port_refresh()
        self._apply_styles()
        
        logger.info("Main window initialized")
    
    def _setup_window(self) -> None:
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setGeometry(100, 100, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self._load_window_icon()
    
    def _load_window_icon(self) -> None:
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
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        main_layout.addWidget(self._create_header())
        main_layout.addLayout(self._create_content_layout(), 1)
    
    def _create_header(self) -> QWidget:
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)
        
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
        subtitle_label.setStyleSheet("color: #8C8984; font-size: 10pt; font-weight: 500;")
        layout.addWidget(subtitle_label)
        
        return layout
    
    def _create_status_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(8)
        
        self._connection_card = StatusCard("Conexión", "Desconectado", "disconnected")
        layout.addWidget(self._connection_card)
        
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
        layout.addWidget(self._create_middle_panel(), 1)
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
        
        self._lighting_panel.lighting_changed.connect(self._on_lighting_changed)
        
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
    
    def _start_port_refresh(self) -> None:
        self._port_refresh_timer.timeout.connect(self._refresh_ports)
        self._port_refresh_timer.start(self.PORT_REFRESH_INTERVAL)
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
        elif status == ConnectionStatus.CONNECTING:
            self._connection_card.set_value("Conectando...", "connecting")
        elif status == ConnectionStatus.ERROR:
            self._connection_card.set_value("Error", "disconnected")
        else:
            self._connection_panel.set_connect_button_text("Conectar")
            self._connection_panel.connect_button.setObjectName("")
            style_manager._refresh_widget_style(self._connection_panel.connect_button)
            self._connection_card.set_value("Desconectado", "disconnected")
            self._photo_panel.set_system_info("Desconectado", "disconnected")
    
    def _on_lighting_changed(self, channel: str, intensity: int) -> None:
        self._preset_panel.clear_selection()
        
        if self._session_controller.is_connected:
            success = self._session_controller.set_lighting(channel, intensity)
            ring_index = settings.lighting_channels.index(channel) if channel in settings.lighting_channels else -1
            if success:
                normalized = intensity / 255.0
                self._log_panel.add_message(f"Anillo {ring_index + 1} configurado a {normalized:.2f}")
            else:
                self._log_panel.add_message(f"Error al configurar Anillo {ring_index + 1}", is_error=True)
    
    def _on_preset_selected(self, preset_name: str, preset_values: dict[str, int]) -> None:
        self._lighting_panel.set_all_values(preset_values)
        self._log_panel.add_message(f"Perfil '{preset_name}' aplicado")
    
    def _on_position_forward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Moviendo posición hacia adelante...")
    
    def _on_position_backward(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Moviendo posición hacia atrás...")
    
    def _on_flip_coin(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Volteando moneda...")
    
    def _on_take_photo(self) -> None:
        if not self._check_connected():
            return
        self._log_panel.add_message("Tomando fotografía...")
    
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
        if self._session_controller.is_connected:
            self._session_controller.disconnect()
        
        self._lighting_panel.set_all_values({ch: 0 for ch in settings.lighting_channels})
        self._photo_panel.set_sequence_active(False)
        self._log_panel.add_message("PARADA DE EMERGENCIA ACTIVADA", is_error=True)
        self._photo_panel.set_system_info("Parada de emergencia", "emergency")
    
    def _on_arduino_response(self, response: Response) -> None:
        if response.data and 'led_state' in response.data:
            led_state = response.data['led_state']
            self._photo_panel.set_led_status(led_state)
        
        if response.success:
            self._log_panel.add_message(f"Arduino: {response.message}")
            self._arduino_card.set_value("Operativo", "operational")
        else:
            self._log_panel.add_message(f"Error Arduino: {response.message}", is_error=True)
            self._arduino_card.set_value("Error", "disconnected")
    
    def _check_connected(self) -> bool:
        if not self._session_controller.is_connected:
            QMessageBox.warning(self, "Error", "No conectado a Arduino")
            return False
        return True
    
    def closeEvent(self, event) -> None:
        if self._session_controller.is_connected:
            self._session_controller.disconnect()
        
        self._port_refresh_timer.stop()
        if self._port_refresh_thread.isRunning():
            self._port_refresh_thread.quit()
            self._port_refresh_thread.wait()
        
        event.accept()
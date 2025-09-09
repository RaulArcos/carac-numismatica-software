from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSlider,
    QGroupBox,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QProgressBar,
    QMessageBox,
    QSplitter,
    QFrame,
    QScrollArea,
    QFileDialog,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QIcon, QPixmap

from loguru import logger

from ..config.settings import settings
from ..controllers.session_controller import SessionController
from ..serialio.ports import get_available_ports, get_arduino_ports
from ..protocol.models import ConnectionStatus, Response
from .style_manager import style_manager


class PortRefreshThread(QThread):
    ports_updated = Signal(list)
    
    def run(self):
        ports = get_available_ports()
        self.ports_updated.emit(ports)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.session_controller = SessionController()
        self.port_refresh_timer = QTimer()
        self.port_refresh_thread = PortRefreshThread()
        
        self.setup_ui()
        self.setup_connections()
        self.setup_timers()
        
        self.session_controller.add_status_callback(self.on_connection_status_changed)
        self.session_controller.add_response_callback(self.on_arduino_response)
        
        logger.info("Main window initialized")
    
    def setup_ui(self):
        self.setWindowTitle("CARAC - Control Numismático UCA")
        
        # Set application icon
        # Try different paths for development and packaged app
        possible_icon_paths = [
            Path(__file__).parent.parent.parent.parent / "assets" / "ui" / "logo.png",  # Development
            Path.cwd() / "assets" / "ui" / "logo.png",  # Packaged app
            Path(__file__).parent / "assets" / "ui" / "logo.png",  # Alternative
        ]
        
        for icon_path in possible_icon_paths:
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                logger.info(f"Application icon loaded from: {icon_path}")
                break
        else:
            logger.warning("Application icon not found")
        
        # Make window compact and responsive
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(900, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with compact margins
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header section
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Left panel - Activity log (smaller space)
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)  # Smaller space for activity log
        
        # Right panel with controls (larger space, no scroll)
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 2)  # More space for controls
        
        main_layout.addLayout(content_layout, 1)
        
        self.apply_styles()
    
    def create_header(self) -> QWidget:
        """Create modern header with title and status cards"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        
        # Title section
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("CARAC - Control Numismático")
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Universidad de Cádiz")
        subtitle_label.setStyleSheet("color: #8C8984; font-size: 10pt; font-weight: 500;")
        title_layout.addWidget(subtitle_label)
        
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        
        # Status cards section (similar to dashboard)
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        
        # Connection status card
        self.connection_card = self.create_status_card("Conexión", "Desconectado", "#dc3545")
        status_layout.addWidget(self.connection_card)
        
        # Arduino status card
        self.arduino_card = self.create_status_card("Estado Arduino", "Sin datos", "#8C8984")
        status_layout.addWidget(self.arduino_card)
        
        # Photo count card
        self.photo_card = self.create_status_card("Fotos Tomadas", "0", "#00607C")
        status_layout.addWidget(self.photo_card)
        
        status_layout.addStretch()
        header_layout.addLayout(status_layout)
        
        return header_widget
    
    def create_status_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a status card similar to the dashboard image"""
        card = QFrame()
        card.setFrameStyle(QFrame.NoFrame)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-radius: 8px;
                margin: 2px;
            }
        """)
        card.setMinimumSize(150, 70)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        style_manager.set_card_title_style(title_label)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        # Set initial state based on the value/color
        initial_state = "disconnected" if "Desconectado" in value else "inactive"
        style_manager.apply_card_value_style(value_label, initial_state)
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
    
    def create_left_panel(self) -> QWidget:
        """Create left panel with activity log"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Activity log - takes up most space
        log_group = QGroupBox("Registro de Actividad")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        return panel
    
    def create_connection_group(self) -> QGroupBox:
        group = QGroupBox("Conexión Arduino")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Port selection row
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto:"))
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setToolTip("Selecciona el puerto de comunicación Arduino")
        port_layout.addWidget(self.port_combo, 1)
        
        self.refresh_button = QPushButton("↻")
        style_manager.apply_button_style(self.refresh_button, "secondary")
        self.refresh_button.setMaximumWidth(40)
        self.refresh_button.setToolTip("Actualizar lista de puertos")
        port_layout.addWidget(self.refresh_button)
        layout.addLayout(port_layout)
        
        # Baud rate row
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Velocidad:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        baud_layout.addWidget(self.baud_combo, 1)
        layout.addLayout(baud_layout)
        
        # Connection button
        self.connect_button = QPushButton("Conectar")
        self.connect_button.setMinimumHeight(30)
        layout.addWidget(self.connect_button)
        
        return group
    
    def create_lighting_group(self) -> QGroupBox:
        group = QGroupBox("Control de Iluminación")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        self.lighting_controls = {}
        
        # Channel names in Spanish
        channel_names = {
            "top": "Superior",
            "bottom": "Inferior", 
            "left": "Izquierda",
            "right": "Derecha",
            "ambient": "Ambiente"
        }
        
        for channel in settings.lighting_channels:
            channel_container = QFrame()
            channel_container.setStyleSheet("""
                QFrame {
                    background: #f8f9fa;
                    border-radius: 6px;
                    padding: 6px;
                    margin: 1px;
                }
            """)
            
            channel_layout = QVBoxLayout(channel_container)
            channel_layout.setSpacing(4)
            
            # Channel name and value in one compact line
            header_layout = QHBoxLayout()
            channel_name = channel_names.get(channel, channel.title())
            label = QLabel(channel_name)
            label.setStyleSheet("font-weight: 600; color: #00607C; font-size: 8pt;")
            header_layout.addWidget(label)
            
            value_label = QLabel("0")
            value_label.setMinimumWidth(30)
            value_label.setAlignment(Qt.AlignRight)
            value_label.setStyleSheet("font-weight: 600; color: #2c3e50; font-size: 8pt;")
            header_layout.addWidget(value_label)
            channel_layout.addLayout(header_layout)
            
            # Compact slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, settings.max_lighting_intensity)
            slider.setValue(0)
            slider.setMinimumHeight(20)
            channel_layout.addWidget(slider)
            
            layout.addWidget(channel_container)
            
            self.lighting_controls[channel] = {
                "slider": slider,
                "value_label": value_label
            }
        
        return group
    
    def create_photo_group(self) -> QGroupBox:
        group = QGroupBox("Secuencia de Fotos")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Compact settings container
        settings_container = QFrame()
        settings_container.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border-radius: 6px;
                padding: 8px;
                margin: 1px;
            }
        """)
        settings_layout = QGridLayout(settings_container)
        settings_layout.setSpacing(6)
        
        # Make labels smaller
        qty_label = QLabel("Cantidad:")
        qty_label.setStyleSheet("font-size: 8pt;")
        settings_layout.addWidget(qty_label, 0, 0)
        
        self.photo_count_spin = QSpinBox()
        self.photo_count_spin.setRange(1, 100)
        self.photo_count_spin.setValue(settings.photo_sequence_count)
        self.photo_count_spin.setMinimumHeight(25)
        settings_layout.addWidget(self.photo_count_spin, 0, 1)
        
        interval_label = QLabel("Intervalo (s):")
        interval_label.setStyleSheet("font-size: 8pt;")
        settings_layout.addWidget(interval_label, 1, 0)
        
        self.photo_delay_spin = QDoubleSpinBox()
        self.photo_delay_spin.setRange(0.1, 10.0)
        self.photo_delay_spin.setValue(settings.photo_sequence_delay)
        self.photo_delay_spin.setSingleStep(0.1)
        self.photo_delay_spin.setMinimumHeight(25)
        settings_layout.addWidget(self.photo_delay_spin, 1, 1)
        
        layout.addWidget(settings_container)
        
        # Action buttons in a compact layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(4)
        
        self.start_photo_button = QPushButton("Iniciar Secuencia")
        style_manager.apply_button_style(self.start_photo_button, "start")
        self.start_photo_button.setMinimumHeight(30)
        buttons_layout.addWidget(self.start_photo_button)
        
        # LED button with status indicator layout
        led_layout = QHBoxLayout()
        
        self.toggle_led_button = QPushButton("LED de Prueba")
        style_manager.apply_button_style(self.toggle_led_button, "warning")
        self.toggle_led_button.setMinimumHeight(25)
        led_layout.addWidget(self.toggle_led_button)
        
        # LED status indicator
        self.led_status_label = QLabel("●")
        self.led_status_label.setFixedSize(20, 20)
        self.led_status_label.setAlignment(Qt.AlignCenter)
        self.led_status_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
        """)
        self.led_status_label.setToolTip("Estado del LED L del Arduino")
        led_layout.addWidget(self.led_status_label)
        
        buttons_layout.addLayout(led_layout)
        
        layout.addLayout(buttons_layout)
        
        return group
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with all controls in a compact layout"""
        panel = QWidget()
        main_layout = QHBoxLayout(panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Left column
        left_column = QVBoxLayout()
        left_column.setSpacing(6)
        
        # Connection controls
        connection_group = self.create_connection_group()
        left_column.addWidget(connection_group)
        
        # Photo controls
        photo_group = self.create_photo_group()
        left_column.addWidget(photo_group)
        
        left_column.addStretch()
        
        # Right column
        right_column = QVBoxLayout()
        right_column.setSpacing(6)
        
        # Lighting controls
        lighting_group = self.create_lighting_group()
        right_column.addWidget(lighting_group)
        
        # Quick controls section
        controls_group = QGroupBox("Controles Rápidos")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(6)
        
        # Emergency stop button
        self.emergency_stop_button = QPushButton("PARADA DE EMERGENCIA")
        style_manager.apply_button_style(self.emergency_stop_button, "emergency")
        self.emergency_stop_button.setMinimumHeight(35)
        controls_layout.addWidget(self.emergency_stop_button)
        
        # Log control buttons in a row
        log_buttons_layout = QHBoxLayout()
        log_buttons_layout.setSpacing(4)
        
        clear_log_button = QPushButton("Limpiar Registro")
        style_manager.apply_button_style(clear_log_button, "secondary")
        clear_log_button.clicked.connect(self.clear_log)
        log_buttons_layout.addWidget(clear_log_button)
        
        save_log_button = QPushButton("Guardar Registro")
        style_manager.apply_button_style(save_log_button, "secondary")
        save_log_button.clicked.connect(self.save_log)
        log_buttons_layout.addWidget(save_log_button)
        
        controls_layout.addLayout(log_buttons_layout)
        
        # System info display
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Estado:"))
        self.system_info_label = QLabel("Iniciado")
        style_manager.apply_system_info_style(self.system_info_label, "normal")
        info_layout.addWidget(self.system_info_label)
        info_layout.addStretch()
        controls_layout.addLayout(info_layout)
        
        right_column.addWidget(controls_group)
        right_column.addStretch()
        
        # Add columns to main layout
        main_layout.addLayout(left_column)
        main_layout.addLayout(right_column)
        
        return panel
    
    def setup_connections(self):
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.toggle_connection)
        
        for channel, controls in self.lighting_controls.items():
            slider = controls["slider"]
            value_label = controls["value_label"]
            
            slider.valueChanged.connect(
                lambda value, ch=channel, label=value_label: self.on_lighting_changed(ch, value, label)
            )
        
        self.start_photo_button.clicked.connect(self.start_photo_sequence)
        
        self.toggle_led_button.clicked.connect(self.toggle_test_led)
        
        # Connect emergency stop button
        self.emergency_stop_button.clicked.connect(self.emergency_stop)
        
        self.port_refresh_thread.ports_updated.connect(self.update_port_list)
    
    def setup_timers(self):
        self.port_refresh_timer.timeout.connect(self.refresh_ports)
        self.port_refresh_timer.start(5000)
        
        self.refresh_ports()
    
    def apply_styles(self):
        """Apply the complete stylesheet using the style manager"""
        stylesheet = style_manager.get_combined_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
            logger.info("Applied combined stylesheet successfully")
        else:
            logger.warning("No stylesheet available, using fallback")
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #f8f9fa, stop: 1 #e9ecef);
                    color: #2c3e50;
                }
            """)
    
    def refresh_ports(self):
        if not self.port_refresh_thread.isRunning():
            self.port_refresh_thread.start()
    
    def update_port_list(self, ports: list):
        current_port = self.port_combo.currentText()
        
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        
        if current_port and current_port in ports:
            self.port_combo.setCurrentText(current_port)
        
        arduino_ports = get_arduino_ports()
        for i in range(self.port_combo.count()):
            port = self.port_combo.itemText(i)
            if port in arduino_ports:
                self.port_combo.setItemText(i, f"{port} (Arduino)")
    
    def toggle_connection(self):
        if self.session_controller.is_connected:
            self.session_controller.disconnect()
        else:
            self.connect_to_arduino()
    
    def connect_to_arduino(self):
        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Error", "Por favor selecciona un puerto")
            return
        
        port = port.replace(" (Arduino)", "")
        
        try:
            baud_rate = int(self.baud_combo.currentText())
        except ValueError:
            baud_rate = 9600
        
        self.log_message(f"Conectando a {port} a {baud_rate} baud...")
        
        success = self.session_controller.connect(port, baud_rate)
        
        if success:
            self.log_message("Conectado exitosamente")
        else:
            self.log_message("Error de conexión", error=True)
    
    def on_connection_status_changed(self, status: ConnectionStatus):
        if status == ConnectionStatus.CONNECTED:
            self.connect_button.setText("Desconectar")
            style_manager.apply_button_style(self.connect_button, "disconnect")
            
            # Update header card
            self.connection_card.value_label.setText("Conectado")
            style_manager.apply_card_value_style(self.connection_card.value_label, "connected")
            
            # Update system info
            self.system_info_label.setText("Conectado")
            style_manager.apply_system_info_style(self.system_info_label, "connected")
            
        elif status == ConnectionStatus.CONNECTING:
            self.connection_card.value_label.setText("Conectando...")
            style_manager.apply_card_value_style(self.connection_card.value_label, "connecting")
            
        elif status == ConnectionStatus.ERROR:
            self.connection_card.value_label.setText("Error")
            style_manager.apply_card_value_style(self.connection_card.value_label, "disconnected")
            
        else:
            self.connect_button.setText("Conectar")
            self.connect_button.setObjectName("")  # Reset to default button style
            style_manager._refresh_widget_style(self.connect_button)
            
            # Update header card
            self.connection_card.value_label.setText("Desconectado")
            style_manager.apply_card_value_style(self.connection_card.value_label, "disconnected")
            
            # Update system info
            self.system_info_label.setText("Desconectado")
            style_manager.apply_system_info_style(self.system_info_label, "disconnected")
    
    def on_lighting_changed(self, channel: str, value: int, label: QLabel):
        label.setText(str(value))
        
        if self.session_controller.is_connected:
            success = self.session_controller.set_lighting(channel, value)
            if success:
                self.log_message(f"Iluminación {channel} configurada a {value}")
            else:
                self.log_message(f"Error al configurar iluminación {channel}", error=True)
    
    def start_photo_sequence(self):
        if not self.session_controller.is_connected:
            QMessageBox.warning(self, "Error", "No conectado a Arduino")
            return
        
        count = self.photo_count_spin.value()
        delay = self.photo_delay_spin.value()
        
        self.log_message(f"Iniciando secuencia: {count} fotos, intervalo {delay}s")
        
        success = self.session_controller.start_photo_sequence(count, delay)
        
        if success:
            self.log_message("Secuencia de fotos iniciada")
            # Update photo count card
            self.photo_card.value_label.setText("En progreso")
            style_manager.apply_card_value_style(self.photo_card.value_label, "progress")
        else:
            self.log_message("Error al iniciar secuencia de fotos", error=True)
    
    def toggle_test_led(self):
        if not self.session_controller.is_connected:
            QMessageBox.warning(self, "Error", "No conectado a Arduino")
            return
        
        self.log_message("Alternando LED de prueba...")
        
        response = self.session_controller.toggle_led()
        
        if response and response.success:
            # Extract LED state from response data
            led_state = response.data.get('led_state', False) if response.data else False
            self.update_led_status(led_state)
            
            state_text = "encendido" if led_state else "apagado"
            self.log_message(f"LED de prueba {state_text}")
        else:
            self.log_message("Error al alternar LED de prueba", error=True)
    
    def update_led_status(self, led_on: bool):
        """Update the LED status indicator in the UI"""
        if led_on:
            # Green for LED ON
            self.led_status_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 10px;
                    background-color: #4CAF50;
                }
            """)
            self.led_status_label.setToolTip("LED L encendido")
        else:
            # Gray for LED OFF
            self.led_status_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 10px;
                    background-color: #f0f0f0;
                }
            """)
            self.led_status_label.setToolTip("LED L apagado")
    
    def on_arduino_response(self, response: Response):
        # Update LED status if present in response
        if response.data and 'led_state' in response.data:
            led_state = response.data['led_state']
            self.update_led_status(led_state)
            
        # Always log raw data if available for debugging
        if "raw" in response.data:
            raw_data = response.data["raw"]
            # Show raw data with special formatting
            self.log_message(f"RAW: '{raw_data}' (len={len(raw_data)}, bytes={[ord(c) for c in raw_data[:20]]})", error=True)
        
        if response.success:
            self.log_message(f"Arduino: {response.message}")
            # Update Arduino status card
            self.arduino_card.value_label.setText("Operativo")
            style_manager.apply_card_value_style(self.arduino_card.value_label, "operational")
        else:
            self.log_message(f"Error Arduino: {response.message}", error=True)
            self.arduino_card.value_label.setText("Error")
            style_manager.apply_card_value_style(self.arduino_card.value_label, "disconnected")
    
    def log_message(self, message: str, error: bool = False):
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = "ERROR" if error else "INFO"
        color = "red" if error else "black"
        
        log_entry = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color};">{level}: {message}</span>'
        
        self.log_text.append(log_entry)
        
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        if self.session_controller.is_connected:
            self.session_controller.disconnect()
        
        self.port_refresh_timer.stop()
        if self.port_refresh_thread.isRunning():
            self.port_refresh_thread.quit()
            self.port_refresh_thread.wait()
        
        event.accept()
    
    def update_photo_count(self, count: int):
        """Update the photo count in the header card"""
        self.photo_card.value_label.setText(str(count))
        if count > 0:
            style_manager.apply_card_value_style(self.photo_card.value_label, "default")
        else:
            style_manager.apply_card_value_style(self.photo_card.value_label, "inactive")
    
    def emergency_stop(self):
        """Emergency stop function"""
        if self.session_controller.is_connected:
            self.session_controller.disconnect()
        
        # Reset all lighting
        for channel, controls in self.lighting_controls.items():
            controls["slider"].setValue(0)
            controls["value_label"].setText("0")
        
        self.log_message("PARADA DE EMERGENCIA ACTIVADA", error=True)
        self.system_info_label.setText("Parada de emergencia")
        style_manager.apply_system_info_style(self.system_info_label, "emergency")
    
    def clear_log(self):
        """Clear the activity log"""
        self.log_text.clear()
        self.log_message("Registro de actividad limpiado")
    
    def save_log(self):
        """Save the activity log to a file"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Registro de Actividad",
            f"registro_carac_{timestamp}.txt",
            "Archivos de texto (*.txt);;Todos los archivos (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Registro de Actividad - CARAC UCA\n")
                    f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*50 + "\n\n")
                    f.write(self.log_text.toPlainText())
                
                self.log_message(f"Registro guardado en: {filename}")
            except Exception as e:
                self.log_message(f"Error al guardar registro: {str(e)}", error=True)

from typing import Optional
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
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QIcon

from loguru import logger

from ..config.settings import settings
from ..controllers.session_controller import SessionController
from ..serialio.ports import get_available_ports, get_arduino_ports
from ..protocol.models import ConnectionStatus, Response


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
        self.setWindowTitle("Carac - Numismatic Machine Control")
        self.setGeometry(100, 100, settings.window_width, settings.window_height)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 300])
        
        self.apply_styles()
    
    def create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        connection_group = self.create_connection_group()
        layout.addWidget(connection_group)
        
        lighting_group = self.create_lighting_group()
        layout.addWidget(lighting_group)
        
        photo_group = self.create_photo_group()
        layout.addWidget(photo_group)
        
        layout.addStretch()
        return panel
    
    def create_connection_group(self) -> QGroupBox:
        group = QGroupBox("Connection")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        layout.addWidget(self.port_combo, 0, 1)
        
        self.refresh_button = QPushButton("Refresh")
        layout.addWidget(self.refresh_button, 0, 2)
        
        layout.addWidget(QLabel("Baud Rate:"), 1, 0)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        layout.addWidget(self.baud_combo, 1, 1)
        
        self.connect_button = QPushButton("Connect")
        layout.addWidget(self.connect_button, 1, 2)
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.status_label, 2, 0, 1, 3)
        
        return group
    
    def create_lighting_group(self) -> QGroupBox:
        group = QGroupBox("Lighting Control")
        layout = QVBoxLayout(group)
        
        self.lighting_controls = {}
        
        for channel in settings.lighting_channels:
            channel_layout = QHBoxLayout()
            
            label = QLabel(channel.title())
            label.setMinimumWidth(80)
            channel_layout.addWidget(label)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, settings.max_lighting_intensity)
            slider.setValue(0)
            channel_layout.addWidget(slider)
            
            value_label = QLabel("0")
            value_label.setMinimumWidth(40)
            value_label.setAlignment(Qt.AlignRight)
            channel_layout.addWidget(value_label)
            
            layout.addLayout(channel_layout)
            
            self.lighting_controls[channel] = {
                "slider": slider,
                "value_label": value_label
            }
        
        return group
    
    def create_photo_group(self) -> QGroupBox:
        group = QGroupBox("Photo Sequence")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("Count:"), 0, 0)
        self.photo_count_spin = QSpinBox()
        self.photo_count_spin.setRange(1, 100)
        self.photo_count_spin.setValue(settings.photo_sequence_count)
        layout.addWidget(self.photo_count_spin, 0, 1)
        
        layout.addWidget(QLabel("Delay (s):"), 1, 0)
        self.photo_delay_spin = QDoubleSpinBox()
        self.photo_delay_spin.setRange(0.1, 10.0)
        self.photo_delay_spin.setValue(settings.photo_sequence_delay)
        self.photo_delay_spin.setSingleStep(0.1)
        layout.addWidget(self.photo_delay_spin, 1, 1)
        
        self.start_photo_button = QPushButton("Start Photo Sequence")
        self.start_photo_button.setStyleSheet("background-color: #4CAF50; color: black; font-weight: bold;")
        layout.addWidget(self.start_photo_button, 2, 0, 1, 2)
        
        return group
    
    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_group)
        
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
        
        self.port_refresh_thread.ports_updated.connect(self.update_port_list)
    
    def setup_timers(self):
        self.port_refresh_timer.timeout.connect(self.refresh_ports)
        self.port_refresh_timer.start(5000)
        
        self.refresh_ports()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                color: black;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: black;
            }
            QPushButton {
                background-color: #0078d4;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                color: black;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #ffffff;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QLabel {
                color: black;
            }
            QTextEdit {
                color: black;
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
            QMessageBox.warning(self, "Error", "Please select a port")
            return
        
        port = port.replace(" (Arduino)", "")
        
        try:
            baud_rate = int(self.baud_combo.currentText())
        except ValueError:
            baud_rate = 9600
        
        self.log_message(f"Connecting to {port} at {baud_rate} baud...")
        
        success = self.session_controller.connect(port, baud_rate)
        
        if success:
            self.log_message("Connected successfully")
        else:
            self.log_message("Connection failed", error=True)
    
    def on_connection_status_changed(self, status: ConnectionStatus):
        if status == ConnectionStatus.CONNECTED:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_button.setText("Disconnect")
            self.connect_button.setStyleSheet("background-color: #d32f2f; color: black; font-weight: bold;")
        elif status == ConnectionStatus.CONNECTING:
            self.status_label.setText("Connecting...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        elif status == ConnectionStatus.ERROR:
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_button.setText("Connect")
            self.connect_button.setStyleSheet("")
    
    def on_lighting_changed(self, channel: str, value: int, label: QLabel):
        label.setText(str(value))
        
        if self.session_controller.is_connected:
            success = self.session_controller.set_lighting(channel, value)
            if success:
                self.log_message(f"Set {channel} lighting to {value}")
            else:
                self.log_message(f"Failed to set {channel} lighting", error=True)
    
    def start_photo_sequence(self):
        if not self.session_controller.is_connected:
            QMessageBox.warning(self, "Error", "Not connected to Arduino")
            return
        
        count = self.photo_count_spin.value()
        delay = self.photo_delay_spin.value()
        
        self.log_message(f"Starting photo sequence: {count} photos, {delay}s delay")
        
        success = self.session_controller.start_photo_sequence(count, delay)
        
        if success:
            self.log_message("Photo sequence started")
        else:
            self.log_message("Failed to start photo sequence", error=True)
    
    def on_arduino_response(self, response: Response):
        if response.success:
            self.log_message(f"Arduino: {response.message}")
        else:
            self.log_message(f"Arduino Error: {response.message}", error=True)
    
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

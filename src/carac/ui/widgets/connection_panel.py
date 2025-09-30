from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QIcon

from typing import List


class ConnectionPanel(QFrame):
    port_refresh_requested = Signal()
    connection_toggle_requested = Signal()
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.setObjectName("connectionPanel")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        self._port_combo = QComboBox()
        self._port_combo.setEditable(True)
        self._port_combo.setMinimumWidth(100)
        self._port_combo.setMaximumWidth(120)
        self._port_combo.setToolTip("Puerto de comunicación")
        layout.addWidget(self._port_combo)
        
        self._refresh_button = QPushButton("⟳")
        self._refresh_button.setObjectName("refreshButton")
        self._refresh_button.setMaximumWidth(35)
        self._refresh_button.setToolTip("Actualizar puertos")
        self._refresh_button.clicked.connect(self.port_refresh_requested.emit)
        layout.addWidget(self._refresh_button)
        
        self._connect_button = QPushButton("Conectar")
        self._connect_button.setMinimumHeight(30)
        self._connect_button.setMinimumWidth(80)
        self._connect_button.clicked.connect(self.connection_toggle_requested.emit)
        layout.addWidget(self._connect_button)
    
    def set_ports(self, ports: List[str]) -> None:
        current_port = self._port_combo.currentText()
        self._port_combo.clear()
        self._port_combo.addItems(ports)
        
        if current_port and current_port in ports:
            self._port_combo.setCurrentText(current_port)
    
    def get_selected_port(self) -> str:
        return self._port_combo.currentText()
    
    def set_connect_button_text(self, text: str) -> None:
        self._connect_button.setText(text)
    
    @property
    def connect_button(self) -> QPushButton:
        return self._connect_button

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QPushButton, QWidget


class ConnectionPanel(QFrame):
    port_refresh_requested = Signal()
    connection_toggle_requested = Signal()
    
    PORT_COMBO_MIN_WIDTH = 100
    PORT_COMBO_MAX_WIDTH = 120
    REFRESH_BUTTON_MAX_WIDTH = 35
    CONNECT_BUTTON_MIN_HEIGHT = 30
    CONNECT_BUTTON_MIN_WIDTH = 80
    LAYOUT_MARGIN = 10
    LAYOUT_MARGIN_VERTICAL = 8
    LAYOUT_SPACING = 6
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        self.setObjectName("connectionPanel")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN_VERTICAL,
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN_VERTICAL
        )
        layout.setSpacing(self.LAYOUT_SPACING)
        
        self._port_combo = QComboBox()
        self._port_combo.setEditable(True)
        self._port_combo.setMinimumWidth(self.PORT_COMBO_MIN_WIDTH)
        self._port_combo.setMaximumWidth(self.PORT_COMBO_MAX_WIDTH)
        self._port_combo.setToolTip("Puerto de comunicación")
        layout.addWidget(self._port_combo)
        
        self._refresh_button = QPushButton("⟳")
        self._refresh_button.setObjectName("refreshButton")
        self._refresh_button.setMaximumWidth(self.REFRESH_BUTTON_MAX_WIDTH)
        self._refresh_button.setToolTip("Actualizar puertos")
        self._refresh_button.clicked.connect(self.port_refresh_requested.emit)
        layout.addWidget(self._refresh_button)
        
        self._connect_button = QPushButton("Conectar")
        self._connect_button.setMinimumHeight(self.CONNECT_BUTTON_MIN_HEIGHT)
        self._connect_button.setMinimumWidth(self.CONNECT_BUTTON_MIN_WIDTH)
        self._connect_button.clicked.connect(self.connection_toggle_requested.emit)
        layout.addWidget(self._connect_button)
    
    def set_ports(self, ports: list[str]) -> None:
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

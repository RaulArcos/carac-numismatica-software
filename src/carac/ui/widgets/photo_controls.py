from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFrame,
    QWidget,
)
from PySide6.QtCore import Signal, Qt

from ..style_manager import style_manager


class PhotoControlPanel(QGroupBox):
    position_forward_requested = Signal()
    position_backward_requested = Signal()
    flip_coin_requested = Signal()
    take_photo_requested = Signal()
    start_sequence_requested = Signal()
    stop_sequence_requested = Signal()
    emergency_stop_requested = Signal()
    led_toggle_requested = Signal()
    
    BUTTON_HEIGHT_SMALL = 26
    BUTTON_HEIGHT_MEDIUM = 28
    BUTTON_HEIGHT_LARGE = 32
    LED_STATUS_SIZE = 20
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Control de Fotografía", parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self._add_individual_controls(layout)
        self._add_separator(layout)
        self._add_sequence_controls(layout)
        self._add_test_controls(layout)
    
    def _add_individual_controls(self, layout: QVBoxLayout) -> None:
        steps_label = QLabel("Controles Individuales")
        steps_label.setObjectName("sectionLabel")
        layout.addWidget(steps_label)
        
        grid = QGridLayout()
        grid.setSpacing(4)
        
        self._position_forward_btn = QPushButton("Posición ▲")
        self._position_forward_btn.setMinimumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._position_forward_btn.setMaximumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._position_forward_btn.clicked.connect(self.position_forward_requested.emit)
        grid.addWidget(self._position_forward_btn, 0, 0)
        
        self._position_backward_btn = QPushButton("Posición ▼")
        self._position_backward_btn.setMinimumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._position_backward_btn.setMaximumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._position_backward_btn.clicked.connect(self.position_backward_requested.emit)
        grid.addWidget(self._position_backward_btn, 0, 1)
        
        self._flip_coin_btn = QPushButton("Voltear Moneda")
        self._flip_coin_btn.setMinimumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._flip_coin_btn.setMaximumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._flip_coin_btn.clicked.connect(self.flip_coin_requested.emit)
        grid.addWidget(self._flip_coin_btn, 1, 0, 1, 2)
        
        self._take_photo_btn = QPushButton("Tomar Foto")
        self._take_photo_btn.setMinimumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._take_photo_btn.setMaximumHeight(self.BUTTON_HEIGHT_MEDIUM)
        self._take_photo_btn.clicked.connect(self.take_photo_requested.emit)
        grid.addWidget(self._take_photo_btn, 2, 0, 1, 2)
        
        layout.addLayout(grid)
    
    def _add_separator(self, layout: QVBoxLayout) -> None:
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)
    
    def _add_sequence_controls(self, layout: QVBoxLayout) -> None:
        sequence_label = QLabel("Secuencia Completa")
        sequence_label.setObjectName("sectionLabel")
        layout.addWidget(sequence_label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        
        self._start_button = QPushButton("Iniciar Secuencia")
        style_manager.apply_button_style(self._start_button, "start")
        self._start_button.setMinimumHeight(self.BUTTON_HEIGHT_LARGE)
        self._start_button.setMaximumHeight(self.BUTTON_HEIGHT_LARGE)
        self._start_button.clicked.connect(self.start_sequence_requested.emit)
        buttons_layout.addWidget(self._start_button)
        
        self._stop_button = QPushButton("Detener")
        style_manager.apply_button_style(self._stop_button, "warning")
        self._stop_button.setMinimumHeight(self.BUTTON_HEIGHT_LARGE)
        self._stop_button.setMaximumHeight(self.BUTTON_HEIGHT_LARGE)
        self._stop_button.setEnabled(False)
        self._stop_button.clicked.connect(self.stop_sequence_requested.emit)
        buttons_layout.addWidget(self._stop_button)
        
        layout.addLayout(buttons_layout)
    
    def _add_test_controls(self, layout: QVBoxLayout) -> None:
        test_layout = QHBoxLayout()
        
        self._toggle_led_button = QPushButton("LED de Prueba")
        style_manager.apply_button_style(self._toggle_led_button, "warning")
        self._toggle_led_button.setMinimumHeight(self.BUTTON_HEIGHT_SMALL)
        self._toggle_led_button.setMaximumHeight(self.BUTTON_HEIGHT_SMALL)
        self._toggle_led_button.clicked.connect(self.led_toggle_requested.emit)
        test_layout.addWidget(self._toggle_led_button)
        
        self._led_status_label = QLabel("●")
        self._led_status_label.setFixedSize(self.LED_STATUS_SIZE, self.LED_STATUS_SIZE)
        self._led_status_label.setAlignment(Qt.AlignCenter)
        self._led_status_label.setObjectName("ledStatusOff")
        self._led_status_label.setToolTip("Estado del LED del Arduino")
        test_layout.addWidget(self._led_status_label)
        
        layout.addLayout(test_layout)
    
    def set_sequence_active(self, active: bool) -> None:
        self._start_button.setEnabled(not active)
        self._stop_button.setEnabled(active)
    
    def set_led_status(self, led_on: bool) -> None:
        if led_on:
            self._led_status_label.setObjectName("ledStatusOn")
            self._led_status_label.setToolTip("LED encendido")
        else:
            self._led_status_label.setObjectName("ledStatusOff")
            self._led_status_label.setToolTip("LED apagado")
        style_manager.refresh_widget_style(self._led_status_label)
    
    def set_system_info(self, text: str, state: str = "normal") -> None:
        """Set system info - currently unused, kept for backwards compatibility."""
        pass

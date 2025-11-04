from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class WeightDisplayWidget(QGroupBox):
    _INITIAL_WEIGHT = 0.0
    _WEIGHT_FORMAT = "{:.2f}"
    _LAYOUT_SPACING = 6
    _LAYOUT_MARGIN = 6
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Medida Peso", parent)
        self._setup_ui()
        self._set_weight(self._INITIAL_WEIGHT)
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(self._LAYOUT_SPACING)
        layout.setContentsMargins(
            self._LAYOUT_MARGIN,
            self._LAYOUT_MARGIN,
            self._LAYOUT_MARGIN,
            self._LAYOUT_MARGIN
        )
        
        self._weight_label = QLabel(self._WEIGHT_FORMAT.format(self._INITIAL_WEIGHT))
        self._weight_label.setObjectName("weightValue")
        self._weight_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._weight_label)
        
        unit_label = QLabel("gramos")
        unit_label.setObjectName("weightUnit")
        unit_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(unit_label)
    
    def _set_weight(self, weight: float) -> None:
        self._weight_label.setText(self._WEIGHT_FORMAT.format(weight))
    
    def set_weight(self, weight: float) -> None:
        self._set_weight(weight)


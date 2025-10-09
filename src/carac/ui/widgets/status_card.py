from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ..style_manager import style_manager


class StatusCard(QFrame):
    MIN_WIDTH = 120
    MIN_HEIGHT = 60
    MAX_WIDTH = 150
    MAX_HEIGHT = 60
    
    def __init__(
        self,
        title: str,
        initial_value: str = "",
        initial_state: str = "inactive",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._setup_ui(title, initial_value, initial_state)
    
    def _setup_ui(self, title: str, initial_value: str, initial_state: str) -> None:
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("statusCard")
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)
        
        self._title_label = QLabel(title)
        style_manager.set_card_title_style(self._title_label)
        layout.addWidget(self._title_label)
        
        self._value_label = QLabel(initial_value)
        style_manager.apply_card_value_style(self._value_label, initial_state)
        layout.addWidget(self._value_label)
    
    def set_value(self, text: str, state: str = "default") -> None:
        self._value_label.setText(text)
        style_manager.apply_card_value_style(self._value_label, state)
    
    @property
    def value(self) -> str:
        return self._value_label.text()

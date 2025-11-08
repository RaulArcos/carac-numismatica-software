from datetime import datetime

from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..style_manager import style_manager


class LogPanel(QGroupBox):
    TIMESTAMP_FORMAT = "%H:%M:%S"
    LEVEL_INFO = "INFO"
    LEVEL_ERROR = "ERROR"
    COLOR_TIMESTAMP = "gray"
    COLOR_INFO = "#2c3e50"
    COLOR_ERROR = "#DD7500"
    MAX_LOG_HEIGHT = 500
    BUTTON_HEIGHT = 20

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Registro", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)
        self._log_text = QTextEdit()
        self._log_text.setObjectName("logText")
        self._log_text.setReadOnly(True)
        self._log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._log_text.setMaximumHeight(self.MAX_LOG_HEIGHT)
        layout.addWidget(self._log_text)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        clear_button = QPushButton("Limpiar")
        clear_button.setMaximumHeight(self.BUTTON_HEIGHT)
        style_manager.apply_button_style(clear_button, "secondary")
        clear_button.clicked.connect(self.clear)
        buttons_layout.addWidget(clear_button)
        save_button = QPushButton("Guardar")
        save_button.setMaximumHeight(self.BUTTON_HEIGHT)
        style_manager.apply_button_style(save_button, "secondary")
        save_button.clicked.connect(self.save)
        buttons_layout.addWidget(save_button)
        layout.addLayout(buttons_layout)

    def add_message(self, message: str, is_error: bool = False) -> None:
        timestamp = datetime.now().strftime(self.TIMESTAMP_FORMAT)
        level = self.LEVEL_ERROR if is_error else self.LEVEL_INFO
        color = self.COLOR_ERROR if is_error else self.COLOR_INFO
        log_entry = (
            f'<span style="color: {self.COLOR_TIMESTAMP};">[{timestamp}]</span> '
            f'<span style="color: {color}; font-weight: 500;">{level}:</span> '
            f'<span style="color: {color};">{message}</span>'
        )
        self._log_text.append(log_entry)
        self._scroll_to_bottom()

    def clear(self) -> None:
        self._log_text.clear()
        self.add_message("Registro limpiado")

    def save(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Registro de Actividad",
            f"registro_carac_{timestamp}.txt",
            "Archivos de texto (*.txt);;Todos los archivos (*.*)",
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("Registro de Actividad - CARAC UCA\n")
                    f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(self._log_text.toPlainText())
                self.add_message(f"Registro guardado en: {filename}")
            except Exception as e:
                self.add_message(f"Error al guardar registro: {str(e)}", is_error=True)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

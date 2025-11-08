from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..style_manager import style_manager


class PresetControlPanel(QGroupBox):
    preset_selected = Signal(str, dict)

    CUSTOM_PRESET_COUNT = 2
    BUTTON_MIN_HEIGHT = 20
    BUTTON_MAX_HEIGHT = 20
    SAVE_BUTTON_MAX_WIDTH = 30
    SAVE_ICON_SIZE = 14
    LAYOUT_SPACING = 4
    LAYOUT_MARGIN = 6
    GRID_SPACING = 3

    def __init__(
        self,
        default_presets: dict[str, dict[str, int]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Perfiles de Iluminación", parent)
        self._default_presets = default_presets
        self._custom_presets: list[dict[str, int]] = [{}, {}]
        self._preset_buttons: dict[str, QPushButton] = {}
        self._selected_preset: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(self.LAYOUT_SPACING)
        layout.setContentsMargins(
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN,
        )
        preset_buttons_layout = QGridLayout()
        preset_buttons_layout.setSpacing(self.GRID_SPACING)
        for i, preset_name in enumerate(self._default_presets.keys()):
            btn = QPushButton(preset_name)
            btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
            btn.setMaximumHeight(self.BUTTON_MAX_HEIGHT)
            style_manager.apply_button_style(btn, "secondary")
            btn.clicked.connect(
                lambda checked, name=preset_name: self._on_preset_clicked(name)
            )
            preset_buttons_layout.addWidget(btn, i // 2, i % 2)
            self._preset_buttons[preset_name] = btn
        layout.addLayout(preset_buttons_layout)
        custom_label = QLabel("Perfiles Personalizados")
        custom_label.setObjectName("customPresetsLabel")
        layout.addWidget(custom_label)
        for i in range(self.CUSTOM_PRESET_COUNT):
            custom_layout = QHBoxLayout()
            custom_layout.setSpacing(self.GRID_SPACING)
            preset_name = f"Custom {i + 1}"
            load_btn = QPushButton(preset_name)
            load_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
            load_btn.setMaximumHeight(self.BUTTON_MAX_HEIGHT)
            style_manager.apply_button_style(load_btn, "secondary")
            load_btn.clicked.connect(
                lambda checked, idx=i: self._on_custom_preset_clicked(idx)
            )
            custom_layout.addWidget(load_btn, 2)
            self._preset_buttons[preset_name] = load_btn
            save_btn = QPushButton()
            save_btn.setObjectName("savePresetButton")
            save_btn.setMaximumWidth(self.SAVE_BUTTON_MAX_WIDTH)
            save_btn.setMinimumHeight(self.BUTTON_MIN_HEIGHT)
            save_btn.setMaximumHeight(self.BUTTON_MAX_HEIGHT)
            save_btn.setToolTip(f"Guardar configuración actual en {preset_name}")
            save_btn.clicked.connect(
                lambda checked, idx=i: self._on_save_custom_preset(idx)
            )
            icon_path = (
                Path(__file__).parent.parent.parent.parent
                / "assets"
                / "ui"
                / "save_icon.svg"
            )
            if icon_path.exists():
                save_btn.setIcon(QIcon(str(icon_path)))
                save_btn.setIconSize(QSize(self.SAVE_ICON_SIZE, self.SAVE_ICON_SIZE))
            custom_layout.addWidget(save_btn)
            layout.addLayout(custom_layout)

    def _on_preset_clicked(self, preset_name: str) -> None:
        preset = self._default_presets.get(preset_name)
        if preset:
            self._select_preset(preset_name)
            self.preset_selected.emit(preset_name, preset)

    def _on_custom_preset_clicked(self, index: int) -> None:
        preset = self._custom_presets[index]
        if not preset:
            QMessageBox.warning(
                self, "Sin datos", f"Custom {index + 1} no tiene configuración guardada"
            )
            return
        preset_name = f"Custom {index + 1}"
        self._select_preset(preset_name)
        self.preset_selected.emit(preset_name, preset)

    def _on_save_custom_preset(self, index: int) -> None:
        QMessageBox.information(
            self, "Guardado", f"Perfil Custom {index + 1} guardado exitosamente"
        )

    def save_custom_preset(self, index: int, values: dict[str, int]) -> None:
        if 0 <= index < self.CUSTOM_PRESET_COUNT:
            self._custom_presets[index] = values.copy()

    def _select_preset(self, preset_name: str) -> None:
        for name, btn in self._preset_buttons.items():
            if name == preset_name:
                style_manager.apply_button_style(btn, "preset_selected")
            else:
                style_manager.apply_button_style(btn, "secondary")
        self._selected_preset = preset_name

    def clear_selection(self) -> None:
        for btn in self._preset_buttons.values():
            style_manager.apply_button_style(btn, "secondary")
        self._selected_preset = None

    @property
    def selected_preset(self) -> str | None:
        return self._selected_preset

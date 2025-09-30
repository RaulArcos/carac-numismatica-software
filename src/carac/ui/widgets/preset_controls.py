from typing import Dict

from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QIcon
from pathlib import Path

from ..style_manager import style_manager


class PresetControlPanel(QGroupBox):
    preset_selected = Signal(str, dict)
    
    CUSTOM_PRESET_COUNT = 2
    
    def __init__(
        self,
        default_presets: Dict[str, Dict[str, int]],
        parent: QWidget | None = None
    ) -> None:
        super().__init__("Perfiles de Iluminación", parent)
        self._default_presets = default_presets
        self._custom_presets: list[Dict[str, int]] = [{}, {}]
        self._preset_buttons: Dict[str, QPushButton] = {}
        self._selected_preset: str | None = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)
        
        preset_buttons_layout = QGridLayout()
        preset_buttons_layout.setSpacing(4)
        
        for i, preset_name in enumerate(self._default_presets.keys()):
            btn = QPushButton(preset_name)
            btn.setMinimumHeight(26)
            btn.setMaximumHeight(26)
            style_manager.apply_button_style(btn, "secondary")
            btn.clicked.connect(lambda checked, name=preset_name: self._on_preset_clicked(name))
            preset_buttons_layout.addWidget(btn, i // 2, i % 2)
            self._preset_buttons[preset_name] = btn
        
        layout.addLayout(preset_buttons_layout)
        
        custom_label = QLabel("Perfiles Personalizados")
        custom_label.setObjectName("customPresetsLabel")
        layout.addWidget(custom_label)
        
        for i in range(self.CUSTOM_PRESET_COUNT):
            custom_layout = QHBoxLayout()
            custom_layout.setSpacing(4)
            
            preset_name = f"Custom {i + 1}"
            load_btn = QPushButton(preset_name)
            load_btn.setMinimumHeight(26)
            load_btn.setMaximumHeight(26)
            style_manager.apply_button_style(load_btn, "secondary")
            load_btn.clicked.connect(lambda checked, idx=i: self._on_custom_preset_clicked(idx))
            custom_layout.addWidget(load_btn, 2)
            self._preset_buttons[preset_name] = load_btn
            
            save_btn = QPushButton()
            save_btn.setObjectName("savePresetButton")
            save_btn.setMaximumWidth(40)
            save_btn.setMinimumHeight(26)
            save_btn.setMaximumHeight(26)
            save_btn.setToolTip(f"Guardar configuración actual en {preset_name}")
            save_btn.clicked.connect(lambda checked, idx=i: self._on_save_custom_preset(idx))
            
            icon_path = Path(__file__).parent.parent.parent.parent / "assets" / "ui" / "save_icon.svg"
            if icon_path.exists():
                save_btn.setIcon(QIcon(str(icon_path)))
                save_btn.setIconSize(QSize(18, 18))
            
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
                self,
                "Sin datos",
                f"Custom {index + 1} no tiene configuración guardada"
            )
            return
        
        preset_name = f"Custom {index + 1}"
        self._select_preset(preset_name)
        self.preset_selected.emit(preset_name, preset)
    
    def _on_save_custom_preset(self, index: int) -> None:
        QMessageBox.information(
            self,
            "Guardado",
            f"Perfil Custom {index + 1} guardado exitosamente"
        )
    
    def save_custom_preset(self, index: int, values: Dict[str, int]) -> None:
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

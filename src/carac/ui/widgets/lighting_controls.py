from typing import Dict, Callable

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSlider,
    QLineEdit,
    QFrame,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from .cylinder_visualization import CylinderVisualization


class LightingControl(QFrame):
    value_changed = Signal(int)
    
    def __init__(
        self,
        ring_name: str,
        ring_number: int,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._ring_number = ring_number
        self._setup_ui(ring_name)
    
    def _setup_ui(self, ring_name: str) -> None:
        self.setObjectName("lightingControlFrame")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)
        
        header_layout = QHBoxLayout()
        name_label = QLabel(ring_name)
        name_label.setObjectName("ringNameLabel")
        header_layout.addWidget(name_label)
        
        self._value_label = QLabel("0")
        self._value_label.setMinimumWidth(30)
        self._value_label.setAlignment(Qt.AlignRight)
        self._value_label.setObjectName("ringValueLabel")
        header_layout.addWidget(self._value_label)
        layout.addLayout(header_layout)
        
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(6)
        
        ring_indicator = QLabel(f"R{self._ring_number}")
        ring_indicator.setObjectName("ringIndicator")
        ring_indicator.setAlignment(Qt.AlignCenter)
        ring_indicator.setFixedWidth(36)
        slider_layout.addWidget(ring_indicator)
        
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setValue(0)
        self._slider.setMinimumHeight(20)
        self._slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self._slider)
        
        self._normalized_input = QLineEdit("0.00")
        self._normalized_input.setMinimumWidth(50)
        self._normalized_input.setMaximumWidth(50)
        self._normalized_input.setAlignment(Qt.AlignCenter)
        self._normalized_input.setObjectName("normalizedInput")
        self._normalized_input.setToolTip("Valor normalizado (0.00 - 1.00)")
        self._normalized_input.editingFinished.connect(self._on_normalized_input_changed)
        slider_layout.addWidget(self._normalized_input)
        
        layout.addLayout(slider_layout)
    
    def _on_slider_changed(self, value: int) -> None:
        normalized = value / 100.0
        intensity_255 = int(normalized * 255)
        
        self._value_label.setText(str(intensity_255))
        
        self._normalized_input.blockSignals(True)
        self._normalized_input.setText(f"{normalized:.2f}")
        self._normalized_input.blockSignals(False)
        
        self.value_changed.emit(intensity_255)
    
    def _on_normalized_input_changed(self) -> None:
        try:
            value = float(self._normalized_input.text().strip())
            value = max(0.0, min(1.0, value))
            
            self._normalized_input.setText(f"{value:.2f}")
            
            slider_value = int(value * 100)
            self._slider.blockSignals(True)
            self._slider.setValue(slider_value)
            self._slider.blockSignals(False)
            
            intensity_255 = int(value * 255)
            self._value_label.setText(str(intensity_255))
            self.value_changed.emit(intensity_255)
        except ValueError:
            slider_value = self._slider.value()
            normalized = slider_value / 100.0
            self._normalized_input.setText(f"{normalized:.2f}")
    
    def set_value(self, intensity: int) -> None:
        intensity = max(0, min(255, intensity))
        value_0_100 = int((intensity / 255.0) * 100)
        normalized = intensity / 255.0
        
        self._slider.blockSignals(True)
        self._slider.setValue(value_0_100)
        self._slider.blockSignals(False)
        
        self._value_label.setText(str(intensity))
        
        self._normalized_input.blockSignals(True)
        self._normalized_input.setText(f"{normalized:.2f}")
        self._normalized_input.blockSignals(False)
    
    def get_value(self) -> int:
        return int(self._slider.value() / 100.0 * 255)


class LightingControlPanel(QGroupBox):
    lighting_changed = Signal(str, int)
    
    def __init__(
        self,
        channels: list[str],
        parent: QWidget | None = None
    ) -> None:
        super().__init__("Iluminación Cilíndrica", parent)
        self._channels = channels
        self._controls: Dict[str, LightingControl] = {}
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)
        
        viz_layout = QVBoxLayout()
        viz_layout.setContentsMargins(0, 0, 0, 0)
        self._cylinder_viz = CylinderVisualization()
        viz_layout.addWidget(self._cylinder_viz, 0, Qt.AlignCenter | Qt.AlignVCenter)
        layout.addLayout(viz_layout)
        
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(5)
        
        ring_names = ["Anillo 1", "Anillo 2", "Anillo 3", "Anillo 4"]
        
        for i, channel in enumerate(self._channels):
            control = LightingControl(ring_names[i], i + 1)
            control.value_changed.connect(
                lambda intensity, ch=channel, idx=i: self._on_control_changed(ch, intensity, idx)
            )
            controls_layout.addWidget(control)
            self._controls[channel] = control
        
        layout.addLayout(controls_layout)
    
    def _on_control_changed(self, channel: str, intensity: int, ring_index: int) -> None:
        self._cylinder_viz.set_ring_intensity(ring_index, intensity)
        self.lighting_changed.emit(channel, intensity)
    
    def set_channel_value(self, channel: str, intensity: int) -> None:
        if channel in self._controls:
            control = self._controls[channel]
            control.blockSignals(True)
            control.set_value(intensity)
            control.blockSignals(False)
            
            ring_index = self._channels.index(channel)
            self._cylinder_viz.set_ring_intensity(ring_index, intensity)
    
    def set_all_values(self, values: Dict[str, int]) -> None:
        for channel, intensity in values.items():
            self.set_channel_value(channel, intensity)
    
    def get_channel_value(self, channel: str) -> int:
        if channel in self._controls:
            return self._controls[channel].get_value()
        return 0
    
    def get_all_values(self) -> Dict[str, int]:
        return {channel: control.get_value() for channel, control in self._controls.items()}

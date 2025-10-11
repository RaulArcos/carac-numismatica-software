from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .cylinder_visualization import CylinderVisualization


class LightingControl(QFrame):
    value_changed = Signal(int)
    
    VALUE_LABEL_MIN_WIDTH = 30
    SECTION_INDICATOR_WIDTH = 36
    NORMALIZED_INPUT_WIDTH = 50
    SLIDER_MIN_HEIGHT = 20
    LAYOUT_SPACING_SMALL = 2
    LAYOUT_SPACING_MEDIUM = 6
    LAYOUT_MARGIN = 4
    MAX_INTENSITY = 255
    SLIDER_MAX = 100
    
    def __init__(
        self,
        section_name: str,
        section_number: int,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._section_number = section_number
        self._setup_ui(section_name)
    
    def _setup_ui(self, section_name: str) -> None:
        self.setObjectName("lightingControlFrame")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(self.LAYOUT_SPACING_SMALL)
        layout.setContentsMargins(
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN,
            self.LAYOUT_MARGIN
        )
        
        header_layout = QHBoxLayout()
        name_label = QLabel(section_name)
        name_label.setObjectName("ringNameLabel")
        header_layout.addWidget(name_label)
        
        self._value_label = QLabel("0")
        self._value_label.setMinimumWidth(self.VALUE_LABEL_MIN_WIDTH)
        self._value_label.setAlignment(Qt.AlignRight)
        self._value_label.setObjectName("ringValueLabel")
        header_layout.addWidget(self._value_label)
        layout.addLayout(header_layout)
        
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(self.LAYOUT_SPACING_MEDIUM)
        
        section_indicator = QLabel(f"S{self._section_number}")
        section_indicator.setObjectName("ringIndicator")
        section_indicator.setAlignment(Qt.AlignCenter)
        section_indicator.setFixedWidth(self.SECTION_INDICATOR_WIDTH)
        slider_layout.addWidget(section_indicator)
        
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, self.SLIDER_MAX)
        self._slider.setValue(0)
        self._slider.setMinimumHeight(self.SLIDER_MIN_HEIGHT)
        self._slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self._slider)
        
        self._normalized_input = QLineEdit("0.00")
        self._normalized_input.setMinimumWidth(self.NORMALIZED_INPUT_WIDTH)
        self._normalized_input.setMaximumWidth(self.NORMALIZED_INPUT_WIDTH)
        self._normalized_input.setAlignment(Qt.AlignCenter)
        self._normalized_input.setObjectName("normalizedInput")
        self._normalized_input.setToolTip("Valor normalizado (0.00 - 1.00)")
        self._normalized_input.editingFinished.connect(self._on_normalized_input_changed)
        slider_layout.addWidget(self._normalized_input)
        
        layout.addLayout(slider_layout)
    
    def _on_slider_changed(self, value: int) -> None:
        normalized = value / self.SLIDER_MAX
        intensity_255 = int(normalized * self.MAX_INTENSITY)
        
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
            
            slider_value = int(value * self.SLIDER_MAX)
            self._slider.blockSignals(True)
            self._slider.setValue(slider_value)
            self._slider.blockSignals(False)
            
            intensity_255 = int(value * self.MAX_INTENSITY)
            self._value_label.setText(str(intensity_255))
            self.value_changed.emit(intensity_255)
        except ValueError:
            slider_value = self._slider.value()
            normalized = slider_value / self.SLIDER_MAX
            self._normalized_input.setText(f"{normalized:.2f}")
    
    def set_value(self, intensity: int) -> None:
        intensity = max(0, min(self.MAX_INTENSITY, intensity))
        value_0_100 = int((intensity / self.MAX_INTENSITY) * self.SLIDER_MAX)
        normalized = intensity / self.MAX_INTENSITY
        
        self._slider.blockSignals(True)
        self._slider.setValue(value_0_100)
        self._slider.blockSignals(False)
        
        self._value_label.setText(str(intensity))
        
        self._normalized_input.blockSignals(True)
        self._normalized_input.setText(f"{normalized:.2f}")
        self._normalized_input.blockSignals(False)
    
    def get_value(self) -> int:
        return int(self._slider.value() / self.SLIDER_MAX * self.MAX_INTENSITY)


class LightingControlPanel(QGroupBox):
    lighting_changed = Signal(str, int)  # channel, intensity
    section_changed = Signal(int, int)  # section_index, intensity
    
    NUM_SECTIONS = 4
    NUM_RINGS = 4
    
    def __init__(
        self,
        channels: list[str],
        parent: QWidget | None = None
    ) -> None:
        super().__init__("Iluminación Cilíndrica", parent)
        self._channels = channels
        self._section_controls: list[LightingControl] = []
        self._section_intensities: list[list[int]] = [[0] * self.NUM_SECTIONS for _ in range(self.NUM_RINGS)]
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
        
        section_names = ["Sección 1", "Sección 2", "Sección 3", "Sección 4"]
        
        for i in range(self.NUM_SECTIONS):
            control = LightingControl(section_names[i], i + 1)
            control.value_changed.connect(
                lambda intensity, idx=i: self._on_section_changed(idx, intensity)
            )
            controls_layout.addWidget(control)
            self._section_controls.append(control)
        
        layout.addLayout(controls_layout)
    
    def _on_section_changed(self, section_index: int, intensity: int) -> None:
        # Update all rings for this section
        for ring_index in range(self.NUM_RINGS):
            self._section_intensities[ring_index][section_index] = intensity
            channel = f"ring{ring_index + 1}_section{section_index + 1}"
            if channel in self._channels:
                self.lighting_changed.emit(channel, intensity)
        
        # Update visualization
        self._cylinder_viz.set_section_intensities(self._section_intensities)
        self.section_changed.emit(section_index, intensity)
    
    def set_channel_value(self, channel: str, intensity: int) -> None:
        # Parse channel like "ring1_section2"
        if "_" in channel:
            parts = channel.split("_")
            if len(parts) == 2 and parts[0].startswith("ring") and parts[1].startswith("section"):
                try:
                    ring_idx = int(parts[0].replace("ring", "")) - 1
                    section_idx = int(parts[1].replace("section", "")) - 1
                    if 0 <= ring_idx < self.NUM_RINGS and 0 <= section_idx < self.NUM_SECTIONS:
                        self._section_intensities[ring_idx][section_idx] = intensity
                        self._cylinder_viz.set_section_intensities(self._section_intensities)
                except (ValueError, IndexError):
                    pass
    
    def set_section_value(self, section_index: int, intensity: int) -> None:
        if 0 <= section_index < self.NUM_SECTIONS:
            control = self._section_controls[section_index]
            control.blockSignals(True)
            control.set_value(intensity)
            control.blockSignals(False)
            
            # Update all rings for this section
            for ring_index in range(self.NUM_RINGS):
                self._section_intensities[ring_index][section_index] = intensity
            
            self._cylinder_viz.set_section_intensities(self._section_intensities)
    
    def set_all_values(self, values: dict[str, int]) -> None:
        # values is a dict of channel -> intensity
        for channel, intensity in values.items():
            self.set_channel_value(channel, intensity)
        
        # Update section sliders to match (use average if sections have different values)
        for section_idx in range(self.NUM_SECTIONS):
            # Get average intensity for this section across all rings
            total = sum(self._section_intensities[ring_idx][section_idx] for ring_idx in range(self.NUM_RINGS))
            avg_intensity = total // self.NUM_RINGS
            
            control = self._section_controls[section_idx]
            control.blockSignals(True)
            control.set_value(avg_intensity)
            control.blockSignals(False)
    
    def get_channel_value(self, channel: str) -> int:
        # Parse channel like "ring1_section2"
        if "_" in channel:
            parts = channel.split("_")
            if len(parts) == 2 and parts[0].startswith("ring") and parts[1].startswith("section"):
                try:
                    ring_idx = int(parts[0].replace("ring", "")) - 1
                    section_idx = int(parts[1].replace("section", "")) - 1
                    if 0 <= ring_idx < self.NUM_RINGS and 0 <= section_idx < self.NUM_SECTIONS:
                        return self._section_intensities[ring_idx][section_idx]
                except (ValueError, IndexError):
                    pass
        return 0
    
    def get_all_values(self) -> dict[str, int]:
        values = {}
        for ring_idx in range(self.NUM_RINGS):
            for section_idx in range(self.NUM_SECTIONS):
                channel = f"ring{ring_idx + 1}_section{section_idx + 1}"
                values[channel] = self._section_intensities[ring_idx][section_idx]
        return values

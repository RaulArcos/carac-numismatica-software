from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF, QPainterPath
from PySide6.QtWidgets import QWidget


class CylinderVisualization(QWidget):
    RING_COUNT = 4
    SECTION_COUNT = 4
    MIN_WIDTH = 120
    MIN_HEIGHT = 200
    MAX_WIDTH = 140
    MAX_HEIGHT = 220
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.setMaximumSize(self.MAX_WIDTH, self.MAX_HEIGHT)
        # Store intensities as [ring][section]
        self._section_intensities: list[list[int]] = [[0] * self.SECTION_COUNT for _ in range(self.RING_COUNT)]
        
    def set_ring_intensity(self, ring_index: int, intensity: int) -> None:
        """Set all sections of a ring to the same intensity (legacy compatibility)"""
        if 0 <= ring_index < self.RING_COUNT:
            for section in range(self.SECTION_COUNT):
                self._section_intensities[ring_index][section] = max(0, min(255, intensity))
            self.update()
    
    def set_section_intensities(self, intensities: list[list[int]]) -> None:
        """Set section intensities for all rings. intensities[ring_index][section_index]"""
        for ring_idx in range(min(len(intensities), self.RING_COUNT)):
            for section_idx in range(min(len(intensities[ring_idx]), self.SECTION_COUNT)):
                self._section_intensities[ring_idx][section_idx] = max(0, min(255, intensities[ring_idx][section_idx]))
        self.update()
    
    def set_all_intensities(self, intensities: list[int]) -> None:
        """Set all sections of all rings (legacy compatibility)"""
        for index, intensity in enumerate(intensities[:self.RING_COUNT]):
            self.set_ring_intensity(index, intensity)
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        self._draw_base(painter)
        self._draw_coin(painter)
        self._draw_rings(painter)
    
    def _draw_base(self, painter: QPainter) -> None:
        center_x = self.width() // 2
        coin_y = self.height() - 45
        base_width = 55
        base_height = 12
        
        base_points = [
            QPointF(center_x - base_width // 2 - 3, coin_y),
            QPointF(center_x + base_width // 2 + 3, coin_y),
            QPointF(center_x + base_width // 2 + 3, coin_y + base_height),
            QPointF(center_x - base_width // 2 - 3, coin_y + base_height),
        ]
        
        painter.setBrush(QBrush(QColor(160, 160, 160)))
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawPolygon(QPolygonF(base_points))
    
    def _draw_coin(self, painter: QPainter) -> None:
        center_x = self.width() // 2
        coin_y = self.height() - 45
        coin_diameter = 35
        coin_width = coin_diameter
        coin_height = coin_diameter // 3
        
        painter.setBrush(QBrush(QColor(221, 117, 0, 220)))
        painter.setPen(QPen(QColor(180, 90, 0), 2))
        painter.drawEllipse(
            int(center_x - coin_width // 2),
            int(coin_y - coin_height // 2),
            coin_width,
            coin_height
        )
    
    def _draw_rings(self, painter: QPainter) -> None:
        center_x = self.width() // 2
        coin_y = self.height() - 45
        ring_spacing = 38
        ring_start_y = coin_y - 30
        ring_width = 70
        ring_height = 18
        ring_thickness = 4  # Thickness of the LED ring perimeter
        
        for i in range(self.RING_COUNT):
            y = ring_start_y - i * ring_spacing
            reversed_index = self.RING_COUNT - 1 - i
            
            # Define the ring rectangle
            ring_rect_x = center_x - ring_width // 2
            ring_rect_y = y - ring_height // 2
            
            # Draw each quadrant section (4 sections divided by a cross)
            # Section 0: Right quadrant (0° to 90°, or -45° to 45° from center right)
            # Section 1: Top quadrant (90° to 180°, or 45° to 135° from center right)
            # Section 2: Left quadrant (180° to 270°, or 135° to 225° from center right)
            # Section 3: Bottom quadrant (270° to 360°, or 225° to 315° from center right)
            
            # Qt uses angles in 1/16th of a degree, starting from 3 o'clock position (right)
            # and going counter-clockwise
            section_angles = [
                (315 * 16, 90 * 16),   # Section 1: Right quadrant (-45° to 45°)
                (45 * 16, 90 * 16),    # Section 2: Top quadrant (45° to 135°)
                (135 * 16, 90 * 16),   # Section 3: Left quadrant (135° to 225°)
                (225 * 16, 90 * 16),   # Section 4: Bottom quadrant (225° to 315°)
            ]
            
            for section_idx in range(self.SECTION_COUNT):
                intensity = self._section_intensities[reversed_index][section_idx]
                alpha = int(255 * (intensity / 255))
                color = QColor(0, 96, 124, alpha)
                
                start_angle, span_angle = section_angles[section_idx]
                
                # Draw outer arc
                painter.setPen(QPen(color, ring_thickness, Qt.SolidLine, Qt.RoundCap))
                painter.setBrush(Qt.NoBrush)
                painter.drawArc(
                    ring_rect_x,
                    ring_rect_y,
                    ring_width,
                    ring_height,
                    start_angle,
                    span_angle
                )
            
            # Draw ring outline (thin border)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 96, 124), 1))
            painter.drawEllipse(
                ring_rect_x,
                ring_rect_y,
                ring_width,
                ring_height
            )
            
            # Draw ring label
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            painter.drawText(
                int(center_x + ring_width // 2 + 8),
                int(y + 5),
                f"R{reversed_index + 1}"
            )

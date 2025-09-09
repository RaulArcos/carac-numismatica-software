"""
Style management for CARAC UCA interface.
Centralizes all styling operations and provides clean API for UI updates.
"""

from pathlib import Path
from typing import Dict, Optional
from loguru import logger


class StyleManager:
    """Manages all styling for the CARAC interface"""
    
    def __init__(self):
        self.qss_path = Path(__file__).parent / "qss"
        self._loaded_styles: Dict[str, str] = {}
        self._load_all_styles()
    
    def _load_all_styles(self):
        """Load all QSS files into memory"""
        qss_files = [
            "uca_theme.qss",
            "status_styles.qss", 
            "button_styles.qss"
        ]
        
        combined_styles = []
        
        for qss_file in qss_files:
            qss_file_path = self.qss_path / qss_file
            try:
                with open(qss_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    combined_styles.append(f"/* {qss_file} */")
                    combined_styles.append(content)
                    combined_styles.append("")
                    logger.debug(f"Loaded stylesheet: {qss_file}")
            except FileNotFoundError:
                logger.warning(f"Could not find stylesheet: {qss_file}")
        
        self._loaded_styles["combined"] = "\n".join(combined_styles)
    
    def get_combined_stylesheet(self) -> str:
        """Get the complete combined stylesheet"""
        return self._loaded_styles.get("combined", "")
    
    def apply_status_style(self, widget, status: str):
        """Apply status-based styling to a widget"""
        status_map = {
            "connected": "statusConnected",
            "disconnected": "statusDisconnected", 
            "connecting": "statusConnecting",
            "error": "statusError"
        }
        
        object_name = status_map.get(status.lower())
        if object_name:
            widget.setObjectName(object_name)
            self._refresh_widget_style(widget)
    
    def apply_system_info_style(self, widget, state: str):
        """Apply system info styling"""
        state_map = {
            "normal": "systemInfoNormal",
            "connected": "systemInfoConnected",
            "disconnected": "systemInfoDisconnected",
            "emergency": "systemInfoEmergency"
        }
        
        object_name = state_map.get(state.lower())
        if object_name:
            widget.setObjectName(object_name)
            self._refresh_widget_style(widget)
    
    def apply_card_value_style(self, widget, state: str):
        """Apply status card value styling"""
        state_map = {
            "connected": "cardValueConnected",
            "disconnected": "cardValueDisconnected",
            "connecting": "cardValueConnecting", 
            "operational": "cardValueOperational",
            "progress": "cardValueProgress",
            "default": "cardValueDefault",
            "inactive": "cardValueInactive"
        }
        
        object_name = state_map.get(state.lower())
        if object_name:
            widget.setObjectName(object_name)
            self._refresh_widget_style(widget)
    
    def apply_button_style(self, widget, button_type: str):
        """Apply button styling"""
        button_map = {
            "disconnect": "disconnectButton",
            "emergency": "emergencyButton", 
            "start": "startButton",
            "warning": "warningButton",
            "secondary": "secondaryButton"
        }
        
        object_name = button_map.get(button_type.lower())
        if object_name:
            widget.setObjectName(object_name)
            self._refresh_widget_style(widget)
    
    def set_card_title_style(self, widget):
        """Apply card title styling"""
        widget.setObjectName("cardTitle")
        self._refresh_widget_style(widget)
    
    def _refresh_widget_style(self, widget):
        """Force widget to refresh its styling"""
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


# Global style manager instance
style_manager = StyleManager()

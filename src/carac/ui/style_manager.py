from pathlib import Path
from typing import Dict

from loguru import logger


class StyleManager:
    QSS_FILES = [
        "uca_theme.qss",
        "status_styles.qss",
        "button_styles.qss",
    ]
    
    def __init__(self) -> None:
        self._qss_path = Path(__file__).parent / "qss"
        self._loaded_styles: Dict[str, str] = {}
        self._load_all_styles()
    
    def _load_all_styles(self) -> None:
        combined_styles = []
        
        for qss_file in self.QSS_FILES:
            qss_file_path = self._qss_path / qss_file
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
        return self._loaded_styles.get("combined", "")
    
    def apply_status_style(self, widget, status: str) -> None:
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
    
    def apply_system_info_style(self, widget, state: str) -> None:
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
    
    def apply_card_value_style(self, widget, state: str) -> None:
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
    
    def apply_button_style(self, widget, button_type: str) -> None:
        button_map = {
            "disconnect": "disconnectButton",
            "emergency": "emergencyButton",
            "start": "startButton",
            "warning": "warningButton",
            "secondary": "secondaryButton",
            "preset_selected": "presetSelectedButton"
        }
        
        object_name = button_map.get(button_type.lower())
        if object_name:
            widget.setObjectName(object_name)
            self._refresh_widget_style(widget)
    
    def set_card_title_style(self, widget) -> None:
        widget.setObjectName("cardTitle")
        self._refresh_widget_style(widget)
    
    def _refresh_widget_style(self, widget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


style_manager = StyleManager()
from pathlib import Path
from typing import Dict

from loguru import logger


class StyleManager:
    QSS_FILES = [
        "uca_theme.qss",
        "status_styles.qss",
        "button_styles.qss",
    ]

    STATUS_STYLES = {
        "connected": "statusConnected",
        "disconnected": "statusDisconnected",
        "connecting": "statusConnecting",
        "error": "statusError"
    }

    SYSTEM_INFO_STYLES = {
        "normal": "systemInfoNormal",
        "connected": "systemInfoConnected",
        "disconnected": "systemInfoDisconnected",
        "emergency": "systemInfoEmergency"
    }

    CARD_VALUE_STYLES = {
        "connected": "cardValueConnected",
        "disconnected": "cardValueDisconnected",
        "connecting": "cardValueConnecting",
        "operational": "cardValueOperational",
        "progress": "cardValueProgress",
        "default": "cardValueDefault",
        "inactive": "cardValueInactive"
    }

    BUTTON_STYLES = {
        "disconnect": "disconnectButton",
        "emergency": "emergencyButton",
        "start": "startButton",
        "warning": "warningButton",
        "secondary": "secondaryButton",
        "preset_selected": "presetSelectedButton"
    }

    def __init__(self) -> None:
        self._qss_path = Path(__file__).parent / "qss"
        self._loaded_styles: Dict[str, str] = {}
        self._load_all_styles()

    def _load_all_styles(self) -> None:
        combined_styles = []

        for qss_file in self.QSS_FILES:
            content = self._load_single_stylesheet(qss_file)
            if content:
                combined_styles.append(f"/* {qss_file} */")
                combined_styles.append(content)
                combined_styles.append("")

        self._loaded_styles["combined"] = "\n".join(combined_styles)

    def _load_single_stylesheet(self, qss_file: str) -> str:
        qss_file_path = self._qss_path / qss_file
        try:
            with open(qss_file_path, 'r', encoding='utf-8') as f:
                logger.debug(f"Loaded stylesheet: {qss_file}")
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Could not find stylesheet: {qss_file}")
            return ""

    def get_combined_stylesheet(self) -> str:
        return self._loaded_styles.get("combined", "")
    
    def apply_status_style(self, widget, status: str) -> None:
        self._apply_style_from_map(widget, status.lower(), self.STATUS_STYLES)

    def apply_system_info_style(self, widget, state: str) -> None:
        self._apply_style_from_map(widget, state.lower(), self.SYSTEM_INFO_STYLES)

    def apply_card_value_style(self, widget, state: str) -> None:
        self._apply_style_from_map(widget, state.lower(), self.CARD_VALUE_STYLES)

    def apply_button_style(self, widget, button_type: str) -> None:
        self._apply_style_from_map(widget, button_type.lower(), self.BUTTON_STYLES)

    def set_card_title_style(self, widget) -> None:
        widget.setObjectName("cardTitle")
        self.refresh_widget_style(widget)

    def _apply_style_from_map(self, widget, key: str, style_map: Dict[str, str]) -> None:
        object_name = style_map.get(key)
        if object_name:
            widget.setObjectName(object_name)
            self.refresh_widget_style(widget)

    def refresh_widget_style(self, widget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


style_manager = StyleManager()
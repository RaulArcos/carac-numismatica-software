from pathlib import Path

from loguru import logger


class StyleManager:
    QSS_FILES = ["uca_theme.qss", "status_styles.qss", "button_styles.qss"]
    STYLE_MAPS = {
        "status": {
            "connected": "statusConnected",
            "disconnected": "statusDisconnected",
            "connecting": "statusConnecting",
            "error": "statusError"
        },
        "system_info": {
            "normal": "systemInfoNormal",
            "connected": "systemInfoConnected",
            "disconnected": "systemInfoDisconnected",
            "emergency": "systemInfoEmergency"
        },
        "card_value": {
            "connected": "cardValueConnected",
            "disconnected": "cardValueDisconnected",
            "connecting": "cardValueConnecting",
            "operational": "cardValueOperational",
            "progress": "cardValueProgress",
            "default": "cardValueDefault",
            "inactive": "cardValueInactive"
        },
        "button": {
            "disconnect": "disconnectButton",
            "emergency": "emergencyButton",
            "start": "startButton",
            "warning": "warningButton",
            "secondary": "secondaryButton",
            "preset_selected": "presetSelectedButton"
        }
    }

    def __init__(self) -> None:
        qss_path = Path(__file__).parent / "qss"
        combined_styles = []
        for qss_file in self.QSS_FILES:
            try:
                with open(qss_path / qss_file, 'r', encoding='utf-8') as f:
                    logger.debug(f"Loaded stylesheet: {qss_file}")
                    combined_styles.append(f"/* {qss_file} */\n{f.read()}\n")
            except FileNotFoundError:
                logger.warning(f"Could not find stylesheet: {qss_file}")
        self._combined_stylesheet = "\n".join(combined_styles)

    def get_combined_stylesheet(self) -> str:
        return self._combined_stylesheet
    
    def apply_status_style(self, widget, status: str) -> None:
        self._apply_style(widget, status.lower(), "status")

    def apply_system_info_style(self, widget, state: str) -> None:
        self._apply_style(widget, state.lower(), "system_info")

    def apply_card_value_style(self, widget, state: str) -> None:
        self._apply_style(widget, state.lower(), "card_value")

    def apply_button_style(self, widget, button_type: str) -> None:
        self._apply_style(widget, button_type.lower(), "button")

    def set_card_title_style(self, widget) -> None:
        widget.setObjectName("cardTitle")
        self.refresh_widget_style(widget)

    def _apply_style(self, widget, key: str, style_type: str) -> None:
        if object_name := self.STYLE_MAPS[style_type].get(key):
            widget.setObjectName(object_name)
            self.refresh_widget_style(widget)

    def refresh_widget_style(self, widget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


style_manager = StyleManager()
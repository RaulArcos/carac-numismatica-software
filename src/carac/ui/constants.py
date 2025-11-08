from pathlib import Path


class WindowConstants:
    TITLE = "CARAC - Control Numismático UCA"
    ORGANIZATION = "Universidad de Cádiz"
    WIDTH = 1000
    HEIGHT = 650
    X_POS = 100
    Y_POS = 100
    MIN_WIDTH = 900
    MIN_HEIGHT = 580


class LayoutConstants:
    MARGIN = 8
    SPACING = 8
    HEADER_SPACING = 12
    STATUS_CARD_SPACING = 6
    TITLE_SECTION_SPACING = 5
    CONTENT_SPACING = 8
    PANEL_SPACING = 5
    LOG_PANEL_SPACING = 6


class SequenceConstants:
    STEP_COUNT = 4
    WAIT_DELAY_MS = 5000
    RETURN_DELAY_MS = 1000


class ThrottleConstants:
    LOG_DELAY_MS = 50
    WEIGHT_UPDATE_MS = 100


class LightingConstants:
    NORMALIZATION_FACTOR = 255.0


class IconPaths:
    @staticmethod
    def get_logo_paths() -> list[Path]:
        return [
            Path(__file__).parent.parent.parent / "assets" / "ui" / "logo.png",
            Path.cwd() / "assets" / "ui" / "logo.png",
        ]


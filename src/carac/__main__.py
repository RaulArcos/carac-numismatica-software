import sys

from PySide6.QtWidgets import QApplication

from carac.logging_config import setup_logging
from carac.ui.main_window import MainWindow
from carac.version import __version__

APPLICATION_NAME = "Carac"
ORGANIZATION_NAME = "Carac Numismatic Software"


def main() -> None:
    setup_logging()
    
    app = QApplication(sys.argv)
    app.setApplicationName(APPLICATION_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORGANIZATION_NAME)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
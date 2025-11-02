import sys

from PySide6.QtWidgets import QApplication

from carac.logging_config import setup_logging
from carac.ui.main_window import MainWindow
from carac.version import __version__


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Carac")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Carac Numismatic Software")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
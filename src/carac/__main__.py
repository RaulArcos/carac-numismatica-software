import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from carac.logging_config import setup_logging
from carac.ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication


def main() -> None:
    setup_logging()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Carac")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Carac Numismatic Software")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

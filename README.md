# Carac - Numismatic Machine Control Software

A desktop application for controlling a numismatic machine via Arduino serial communication. Built with Python and PySide6 for a native Windows experience.

## Features

- **Serial Communication**: Detect and connect to Arduino via UART
- **Lighting Control**: Control multiple lighting channels (axial, ring, backlight) with sliders
- **Photo Sequence**: Initiate automated photo capture sequences
- **Native UI**: Modern, responsive interface built with PySide6
- **Offline Operation**: Designed to work without internet connection
- **Executable Distribution**: Can be packaged as standalone .exe file

## Requirements

- Python 3.11+
- Windows 10/11
- Arduino-compatible device with serial communication

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/carac-numismastica-software.git
cd carac-numismastica-software
```

2. Install Poetry (if not already installed):
```bash
pip install poetry
```

3. Install dependencies:
```bash
poetry install
```

4. Run the application:
```bash
poetry run carac
```

### Development Setup

1. Install development dependencies:
```bash
poetry install --with dev
```

2. Install pre-commit hooks:
```bash
poetry run pre-commit install
```

3. Run tests:
```bash
poetry run pytest
```

## Usage

1. **Launch the Application**: Run `carac` from the command line or double-click the executable
2. **Connect to Arduino**: Select the appropriate COM port and click "Connect"
3. **Control Lighting**: Use the sliders to adjust lighting intensity for different channels
4. **Photo Sequence**: Click "Start Photo Sequence" to begin automated capture

## Development

### Project Structure

```
carac-numismastica-software/
├── src/carac/           # Main application code
│   ├── config/         # Configuration management
│   ├── protocol/       # Communication protocol models
│   ├── serialio/       # Serial communication
│   ├── controllers/    # Business logic controllers
│   └── ui/            # User interface components
├── tests/             # Test suite
├── packaging/         # PyInstaller configuration
└── scripts/          # Development scripts
```

### Code Quality

- **Linting**: `poetry run ruff check`
- **Type Checking**: `poetry run mypy src/carac`
- **Formatting**: `poetry run ruff format`
- **Testing**: `poetry run pytest`

### Building Executable

```bash
poetry run pyinstaller packaging/pyinstaller/carac.spec
```

The executable will be created in `dist/carac.exe`.

## Configuration

The application uses Pydantic Settings for configuration management. Key settings include:

- Serial port configuration
- Lighting channel definitions
- Logging levels
- UI preferences

## Testing

Run the full test suite:

```bash
poetry run pytest
```

Run specific test categories:

```bash
poetry run pytest -m unit          # Unit tests only
poetry run pytest -m integration   # Integration tests only
poetry run pytest --cov=src/carac  # With coverage report
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass and code quality checks succeed
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PySide6](https://doc.qt.io/qtforpython/) for the user interface
- Serial communication powered by [pyserial](https://pyserial.readthedocs.io/)
- Data validation with [Pydantic](https://pydantic-docs.helpmanual.io/)
- Logging with [Loguru](https://loguru.readthedocs.io/)

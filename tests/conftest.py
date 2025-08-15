"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from carac.config.settings import Settings
from carac.protocol.models import Response, ConnectionStatus
from carac.serialio.arduino_client import ArduinoClient
from carac.controllers.session_controller import SessionController


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        default_baud_rate=9600,
        default_timeout=1.0,
        max_retries=3,
        lighting_channels=["axial", "ring", "backlight"],
        max_lighting_intensity=255,
        window_width=800,
        window_height=600,
        theme="light",
        log_level="DEBUG",
        log_to_file=False,
        log_retention_days=7,
        photo_sequence_delay=1.0,
        photo_sequence_count=5,
    )


@pytest.fixture
def mock_serial():
    """Mock serial connection."""
    mock_serial = Mock()
    mock_serial.is_open = True
    mock_serial.in_waiting = 0
    mock_serial.readline.return_value = b'{"success": true, "message": "OK"}\n'
    return mock_serial


@pytest.fixture
def mock_arduino_client(mock_serial):
    """Mock Arduino client."""
    with patch('carac.serialio.arduino_client.serial.Serial') as mock_serial_class:
        mock_serial_class.return_value = mock_serial
        client = ArduinoClient()
        yield client


@pytest.fixture
def mock_session_controller(mock_arduino_client):
    """Mock session controller."""
    controller = SessionController()
    controller.arduino_client = mock_arduino_client
    return controller


@pytest.fixture
def sample_response():
    """Sample response from Arduino."""
    return Response(
        success=True,
        message="Command executed successfully",
        data={"result": "ok"},
        timestamp=1234567890.0
    )


@pytest.fixture
def sample_ports():
    """Sample serial ports."""
    return ["COM1", "COM3", "COM5"]


@pytest.fixture
def sample_arduino_ports():
    """Sample Arduino ports."""
    return ["COM3"]


@pytest.fixture(scope="session")
def qtbot_session(qtbot):
    """Session-scoped Qt bot for testing."""
    return qtbot

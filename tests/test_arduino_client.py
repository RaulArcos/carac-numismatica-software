"""Tests for Arduino client functionality."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from carac.serialio.arduino_client import ArduinoClient
from carac.protocol.models import (
    Command,
    Response,
    ConnectionStatus,
    PingCommand,
    StatusCommand,
    LightingCommand,
    PhotoSequenceCommand,
)


class TestArduinoClient:
    """Test ArduinoClient class."""
    
    def test_initialization(self):
        """Test client initialization."""
        client = ArduinoClient()
        
        assert client.serial is None
        assert client.status == ConnectionStatus.DISCONNECTED
        assert client._read_thread is None
        assert client._stop_reading is False
        assert client._response_callback is None
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_connect_success(self, mock_serial_class):
        """Test successful connection."""
        # Mock serial connection
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        client = ArduinoClient()
        
        # Mock ping response
        mock_serial.readline.return_value = b'{"success": true, "message": "pong"}\n'
        
        success = client.connect("COM3", 9600)
        
        assert success is True
        assert client.status == ConnectionStatus.CONNECTED
        assert client.serial is not None
        mock_serial_class.assert_called_once_with(
            port="COM3",
            baudrate=9600,
            timeout=1.0,
            write_timeout=1.0,
        )
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_connect_failure(self, mock_serial_class):
        """Test connection failure."""
        mock_serial_class.side_effect = Exception("Connection failed")
        
        client = ArduinoClient()
        success = client.connect("COM3", 9600)
        
        assert success is False
        assert client.status == ConnectionStatus.ERROR
        assert client.serial is None
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_connect_already_connected(self, mock_serial_class):
        """Test connection when already connected."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        client = ArduinoClient()
        client.status = ConnectionStatus.CONNECTED
        client.serial = mock_serial
        
        success = client.connect("COM3", 9600)
        
        assert success is True  # Should return True for already connected
    
    def test_disconnect(self):
        """Test disconnection."""
        client = ArduinoClient()
        
        # Mock connected state
        mock_serial = Mock()
        mock_serial.is_open = True
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        client.disconnect()
        
        assert client.status == ConnectionStatus.DISCONNECTED
        assert client.serial is None
        mock_serial.close.assert_called_once()
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_send_command_success(self, mock_serial_class):
        """Test successful command sending."""
        # Setup mock serial
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        client = ArduinoClient()
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        # Mock response
        mock_serial.readline.return_value = b'{"success": true, "message": "OK"}\n'
        
        command = PingCommand()
        response = client.send_command(command)
        
        assert response is not None
        assert response.success is True
        assert response.message == "OK"
        
        # Verify command was written
        mock_serial.write.assert_called_once()
        mock_serial.flush.assert_called_once()
    
    def test_send_command_not_connected(self):
        """Test sending command when not connected."""
        client = ArduinoClient()
        
        command = PingCommand()
        response = client.send_command(command)
        
        assert response is None
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_send_command_no_response(self, mock_serial_class):
        """Test sending command with no response."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.readline.return_value = b''  # Empty response
        
        client = ArduinoClient()
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        command = PingCommand()
        response = client.send_command(command)
        
        assert response is None
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_ping_success(self, mock_serial_class):
        """Test successful ping."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.readline.return_value = b'{"success": true, "message": "pong"}\n'
        
        client = ArduinoClient()
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        result = client.ping()
        
        assert result is True
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_ping_failure(self, mock_serial_class):
        """Test failed ping."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.readline.return_value = b'{"success": false, "message": "error"}\n'
        
        client = ArduinoClient()
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        result = client.ping()
        
        assert result is False
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_get_status(self, mock_serial_class):
        """Test getting status."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.readline.return_value = b'{"success": true, "message": "status", "data": {"temp": 25}}\n'
        
        client = ArduinoClient()
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        response = client.get_status()
        
        assert response is not None
        assert response.success is True
        assert response.message == "status"
        assert response.data["temp"] == 25
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_set_lighting(self, mock_serial_class):
        """Test setting lighting."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.readline.return_value = b'{"success": true, "message": "lighting set"}\n'
        
        client = ArduinoClient()
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        response = client.set_lighting("axial", 128)
        
        assert response is not None
        assert response.success is True
        assert response.message == "lighting set"
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_start_photo_sequence(self, mock_serial_class):
        """Test starting photo sequence."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.readline.return_value = b'{"success": true, "message": "photo sequence started"}\n'
        
        client = ArduinoClient()
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        response = client.start_photo_sequence(5, 1.0)
        
        assert response is not None
        assert response.success is True
        assert response.message == "photo sequence started"
    
    def test_set_response_callback(self):
        """Test setting response callback."""
        client = ArduinoClient()
        
        def callback(response):
            pass
        
        client.set_response_callback(callback)
        
        assert client._response_callback == callback
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_is_connected_property(self, mock_serial_class):
        """Test is_connected property."""
        client = ArduinoClient()
        
        # Not connected
        assert client.is_connected is False
        
        # Connected
        mock_serial = Mock()
        mock_serial.is_open = True
        client.serial = mock_serial
        client.status = ConnectionStatus.CONNECTED
        
        assert client.is_connected is True
        
        # Serial closed
        mock_serial.is_open = False
        assert client.is_connected is False
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with ArduinoClient() as client:
            assert isinstance(client, ArduinoClient)
            assert client.status == ConnectionStatus.DISCONNECTED


class TestArduinoClientThreading:
    """Test ArduinoClient threading functionality."""
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_read_thread_start(self, mock_serial_class):
        """Test read thread starts on connection."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        client = ArduinoClient()
        
        # Mock ping response
        mock_serial.readline.return_value = b'{"success": true, "message": "pong"}\n'
        
        client.connect("COM3", 9600)
        
        # Thread should be started
        assert client._read_thread is not None
        assert client._read_thread.is_alive()
        
        # Clean up
        client.disconnect()
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_read_thread_stop(self, mock_serial_class):
        """Test read thread stops on disconnect."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial
        
        client = ArduinoClient()
        
        # Mock ping response
        mock_serial.readline.return_value = b'{"success": true, "message": "pong"}\n'
        
        client.connect("COM3", 9600)
        
        # Verify thread is running
        assert client._read_thread.is_alive()
        
        # Disconnect should stop thread
        client.disconnect()
        
        # Thread should be stopped
        assert not client._read_thread.is_alive()
    
    @patch('carac.serialio.arduino_client.serial.Serial')
    def test_async_response_callback(self, mock_serial_class):
        """Test async response callback."""
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.in_waiting = 10  # Simulate data available
        mock_serial.readline.return_value = b'{"success": true, "message": "async"}\n'
        mock_serial_class.return_value = mock_serial
        
        client = ArduinoClient()
        
        # Set up callback
        callback_called = False
        callback_response = None
        
        def callback(response):
            nonlocal callback_called, callback_response
            callback_called = True
            callback_response = response
        
        client.set_response_callback(callback)
        
        # Mock ping response for connection
        mock_serial.readline.return_value = b'{"success": true, "message": "pong"}\n'
        
        client.connect("COM3", 9600)
        
        # Wait a bit for async processing
        time.sleep(0.1)
        
        # Disconnect to stop thread
        client.disconnect()
        
        # Callback should have been called
        assert callback_called
        assert callback_response is not None
        assert callback_response.message == "async"

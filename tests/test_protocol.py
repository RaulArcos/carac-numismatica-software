"""Tests for protocol models."""

import pytest
import json
from datetime import datetime

from carac.protocol.models import (
    Command,
    Response,
    LightingCommand,
    PhotoSequenceCommand,
    PingCommand,
    StatusCommand,
    CommandType,
    ConnectionStatus,
)


class TestCommandType:
    """Test CommandType enum."""
    
    def test_command_types(self):
        """Test all command types are defined."""
        assert CommandType.LIGHTING == "lighting"
        assert CommandType.PHOTO_SEQUENCE == "photo_sequence"
        assert CommandType.PING == "ping"
        assert CommandType.STATUS == "status"


class TestConnectionStatus:
    """Test ConnectionStatus enum."""
    
    def test_connection_statuses(self):
        """Test all connection statuses are defined."""
        assert ConnectionStatus.DISCONNECTED == "disconnected"
        assert ConnectionStatus.CONNECTING == "connecting"
        assert ConnectionStatus.CONNECTED == "connected"
        assert ConnectionStatus.ERROR == "error"


class TestCommand:
    """Test base Command model."""
    
    def test_command_creation(self):
        """Test command creation."""
        command = Command(type=CommandType.PING, data={"test": "value"})
        
        assert command.type == CommandType.PING
        assert command.data == {"test": "value"}
        assert command.timestamp is None
    
    def test_command_to_serial(self):
        """Test command serialization."""
        command = Command(type=CommandType.PING, data={"test": "value"})
        serial_data = command.to_serial()
        
        # Should be valid JSON with newline
        assert serial_data.endswith('\n')
        
        # Parse and verify
        parsed = json.loads(serial_data.strip())
        assert parsed["type"] == "ping"
        assert parsed["data"] == {"test": "value"}


class TestResponse:
    """Test Response model."""
    
    def test_response_creation(self):
        """Test response creation."""
        response = Response(
            success=True,
            message="Test message",
            data={"result": "ok"}
        )
        
        assert response.success is True
        assert response.message == "Test message"
        assert response.data == {"result": "ok"}
        assert response.timestamp is None
    
    def test_response_from_serial_valid(self):
        """Test response deserialization with valid JSON."""
        json_data = '{"success": true, "message": "OK", "data": {"test": "value"}}'
        response = Response.from_serial(json_data)
        
        assert response.success is True
        assert response.message == "OK"
        assert response.data == {"test": "value"}
    
    def test_response_from_serial_invalid(self):
        """Test response deserialization with invalid JSON."""
        invalid_data = "invalid json"
        response = Response.from_serial(invalid_data)
        
        assert response.success is False
        assert "Failed to parse response" in response.message
        assert response.data["raw"] == invalid_data
    
    def test_response_from_serial_empty(self):
        """Test response deserialization with empty data."""
        response = Response.from_serial("")
        
        assert response.success is False
        assert "Failed to parse response" in response.message


class TestLightingCommand:
    """Test LightingCommand model."""
    
    def test_lighting_command_creation(self):
        """Test lighting command creation."""
        command = LightingCommand(channel="axial", intensity=128)
        
        assert command.type == CommandType.LIGHTING
        assert command.channel == "axial"
        assert command.intensity == 128
        assert command.data == {"channel": "axial", "intensity": 128}
    
    def test_lighting_command_validation(self):
        """Test lighting command validation."""
        # Valid intensity
        command = LightingCommand(channel="ring", intensity=255)
        assert command.intensity == 255
        
        # Should clamp to max
        command = LightingCommand(channel="backlight", intensity=300)
        assert command.intensity == 255
        
        # Should clamp to min
        command = LightingCommand(channel="axial", intensity=-10)
        assert command.intensity == 0


class TestPhotoSequenceCommand:
    """Test PhotoSequenceCommand model."""
    
    def test_photo_sequence_command_creation(self):
        """Test photo sequence command creation."""
        command = PhotoSequenceCommand(count=10, delay=2.5)
        
        assert command.type == CommandType.PHOTO_SEQUENCE
        assert command.count == 10
        assert command.delay == 2.5
        assert command.data == {"count": 10, "delay": 2.5}
    
    def test_photo_sequence_command_defaults(self):
        """Test photo sequence command defaults."""
        command = PhotoSequenceCommand()
        
        assert command.count == 5
        assert command.delay == 1.0
    
    def test_photo_sequence_command_validation(self):
        """Test photo sequence command validation."""
        # Valid values
        command = PhotoSequenceCommand(count=50, delay=5.0)
        assert command.count == 50
        assert command.delay == 5.0
        
        # Should clamp count
        command = PhotoSequenceCommand(count=200)
        assert command.count == 100
        
        # Should clamp delay
        command = PhotoSequenceCommand(delay=15.0)
        assert command.delay == 10.0


class TestPingCommand:
    """Test PingCommand model."""
    
    def test_ping_command_creation(self):
        """Test ping command creation."""
        command = PingCommand()
        
        assert command.type == CommandType.PING
        assert command.data == {"ping": True}


class TestStatusCommand:
    """Test StatusCommand model."""
    
    def test_status_command_creation(self):
        """Test status command creation."""
        command = StatusCommand()
        
        assert command.type == CommandType.STATUS
        assert command.data == {"status": True}

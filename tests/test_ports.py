"""Tests for serial ports functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from carac.serialio.ports import (
    get_available_ports,
    get_port_info,
    is_arduino_port,
    get_arduino_ports,
)


class TestGetAvailablePorts:
    """Test get_available_ports function."""
    
    @patch('carac.serialio.ports.serial.tools.list_ports.comports')
    def test_get_available_ports_success(self, mock_comports):
        """Test successful port detection."""
        # Mock port objects
        mock_port1 = Mock()
        mock_port1.device = "COM1"
        
        mock_port2 = Mock()
        mock_port2.device = "COM3"
        
        mock_comports.return_value = [mock_port1, mock_port2]
        
        ports = get_available_ports()
        
        assert ports == ["COM1", "COM3"]
        mock_comports.assert_called_once()
    
    @patch('carac.serialio.ports.serial.tools.list_ports.comports')
    def test_get_available_ports_exception(self, mock_comports):
        """Test port detection with exception."""
        mock_comports.side_effect = Exception("Serial error")
        
        ports = get_available_ports()
        
        assert ports == []
    
    @patch('carac.serialio.ports.serial.tools.list_ports.comports')
    def test_get_available_ports_empty(self, mock_comports):
        """Test port detection with no ports."""
        mock_comports.return_value = []
        
        ports = get_available_ports()
        
        assert ports == []


class TestGetPortInfo:
    """Test get_port_info function."""
    
    @patch('carac.serialio.ports.serial.tools.list_ports.comports')
    def test_get_port_info_success(self, mock_comports):
        """Test successful port info retrieval."""
        # Mock port object
        mock_port = Mock()
        mock_port.device = "COM3"
        mock_port.name = "USB Serial Device"
        mock_port.description = "Arduino Uno"
        mock_port.hwid = "USB VID:PID=2341:0043"
        mock_port.vid = 0x2341
        mock_port.pid = 0x0043
        mock_port.manufacturer = "Arduino LLC"
        mock_port.product = "Arduino Uno"
        
        mock_comports.return_value = [mock_port]
        
        info = get_port_info("COM3")
        
        assert info is not None
        assert info["device"] == "COM3"
        assert info["name"] == "USB Serial Device"
        assert info["description"] == "Arduino Uno"
        assert info["hwid"] == "USB VID:PID=2341:0043"
        assert info["vid"] == 0x2341
        assert info["pid"] == 0x0043
        assert info["manufacturer"] == "Arduino LLC"
        assert info["product"] == "Arduino Uno"
    
    @patch('carac.serialio.ports.serial.tools.list_ports.comports')
    def test_get_port_info_not_found(self, mock_comports):
        """Test port info for non-existent port."""
        mock_port = Mock()
        mock_port.device = "COM1"
        mock_comports.return_value = [mock_port]
        
        info = get_port_info("COM3")
        
        assert info is None
    
    @patch('carac.serialio.ports.serial.tools.list_ports.comports')
    def test_get_port_info_exception(self, mock_comports):
        """Test port info with exception."""
        mock_comports.side_effect = Exception("Serial error")
        
        info = get_port_info("COM3")
        
        assert info is None


class TestIsArduinoPort:
    """Test is_arduino_port function."""
    
    @patch('carac.serialio.ports.get_port_info')
    def test_is_arduino_port_by_description(self, mock_get_port_info):
        """Test Arduino detection by description."""
        mock_get_port_info.return_value = {
            "description": "Arduino Uno",
            "manufacturer": "Some Company",
            "product": "Some Product"
        }
        
        result = is_arduino_port("COM3")
        
        assert result is True
    
    @patch('carac.serialio.ports.get_port_info')
    def test_is_arduino_port_by_manufacturer(self, mock_get_port_info):
        """Test Arduino detection by manufacturer."""
        mock_get_port_info.return_value = {
            "description": "Some Device",
            "manufacturer": "Arduino LLC",
            "product": "Some Product"
        }
        
        result = is_arduino_port("COM3")
        
        assert result is True
    
    @patch('carac.serialio.ports.get_port_info')
    def test_is_arduino_port_by_product(self, mock_get_port_info):
        """Test Arduino detection by product."""
        mock_get_port_info.return_value = {
            "description": "Some Device",
            "manufacturer": "Some Company",
            "product": "Arduino Nano"
        }
        
        result = is_arduino_port("COM3")
        
        assert result is True
    
    @patch('carac.serialio.ports.get_port_info')
    def test_is_arduino_port_ch340(self, mock_get_port_info):
        """Test Arduino detection with CH340."""
        mock_get_port_info.return_value = {
            "description": "USB Serial (CH340)",
            "manufacturer": "Some Company",
            "product": "Some Product"
        }
        
        result = is_arduino_port("COM3")
        
        assert result is True
    
    @patch('carac.serialio.ports.get_port_info')
    def test_is_arduino_port_not_arduino(self, mock_get_port_info):
        """Test non-Arduino device detection."""
        mock_get_port_info.return_value = {
            "description": "Generic USB Device",
            "manufacturer": "Generic Company",
            "product": "Generic Product"
        }
        
        result = is_arduino_port("COM3")
        
        assert result is False
    
    @patch('carac.serialio.ports.get_port_info')
    def test_is_arduino_port_no_info(self, mock_get_port_info):
        """Test Arduino detection with no port info."""
        mock_get_port_info.return_value = None
        
        result = is_arduino_port("COM3")
        
        assert result is False


class TestGetArduinoPorts:
    """Test get_arduino_ports function."""
    
    @patch('carac.serialio.ports.get_available_ports')
    @patch('carac.serialio.ports.is_arduino_port')
    def test_get_arduino_ports_success(self, mock_is_arduino, mock_get_ports):
        """Test successful Arduino port detection."""
        mock_get_ports.return_value = ["COM1", "COM3", "COM5"]
        
        # Mock Arduino detection
        def mock_is_arduino_side_effect(port):
            return port == "COM3"
        
        mock_is_arduino.side_effect = mock_is_arduino_side_effect
        
        arduino_ports = get_arduino_ports()
        
        assert arduino_ports == ["COM3"]
        assert mock_get_ports.call_count == 1
        assert mock_is_arduino.call_count == 3
    
    @patch('carac.serialio.ports.get_available_ports')
    def test_get_arduino_ports_no_ports(self, mock_get_ports):
        """Test Arduino port detection with no ports."""
        mock_get_ports.return_value = []
        
        arduino_ports = get_arduino_ports()
        
        assert arduino_ports == []
    
    @patch('carac.serialio.ports.get_available_ports')
    @patch('carac.serialio.ports.is_arduino_port')
    def test_get_arduino_ports_multiple_arduinos(self, mock_is_arduino, mock_get_ports):
        """Test detection of multiple Arduino ports."""
        mock_get_ports.return_value = ["COM1", "COM3", "COM5", "COM7"]
        
        # Mock Arduino detection
        def mock_is_arduino_side_effect(port):
            return port in ["COM3", "COM7"]
        
        mock_is_arduino.side_effect = mock_is_arduino_side_effect
        
        arduino_ports = get_arduino_ports()
        
        assert arduino_ports == ["COM3", "COM7"]

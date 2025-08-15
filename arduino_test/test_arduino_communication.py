#!/usr/bin/env python3

import json
import time
import serial
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ArduinoResponse:
    success: bool
    message: str
    data: Dict[str, Any]
    timestamp: float


class ArduinoTester:
    
    def __init__(self, port: str, baud_rate: int = 9600, timeout: int = 1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
    
    def connect(self) -> bool:
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            print(f"Connected to Arduino on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to Arduino: {e}")
            return False
    
    def disconnect(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Disconnected from Arduino")
    
    def send_command(self, command_type: str, data: Dict[str, Any] = None) -> Optional[ArduinoResponse]:
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Not connected to Arduino")
            return None
        
        command = {
            "type": command_type,
            "data": data or {},
            "timestamp": time.time()
        }
        
        command_json = json.dumps(command) + "\n"
        print(f"Sending: {command_json.strip()}")
        
        try:
            self.serial_conn.write(command_json.encode('utf-8'))
            self.serial_conn.flush()
            
            response_line = self.serial_conn.readline().decode('utf-8').strip()
            if response_line:
                print(f"Received: {response_line}")
                return self._parse_response(response_line)
            else:
                print("No response received")
                return None
                
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            return None
    
    def _parse_response(self, response_line: str) -> Optional[ArduinoResponse]:
        try:
            response_data = json.loads(response_line)
            return ArduinoResponse(
                success=response_data.get("success", False),
                message=response_data.get("message", ""),
                data=response_data.get("data", {}),
                timestamp=response_data.get("timestamp", 0)
            )
        except json.JSONDecodeError as e:
            print(f"Failed to parse response: {e}")
            return None
    
    def test_ping(self) -> bool:
        print("\n=== Testing Ping Command ===")
        response = self.send_command("ping", {"ping": True})
        if response and response.success:
            print("✅ Ping test passed")
            return True
        else:
            print("❌ Ping test failed")
            return False
    
    def test_status(self) -> bool:
        print("\n=== Testing Status Command ===")
        response = self.send_command("status", {"status": True})
        if response and response.success:
            print("✅ Status test passed")
            print(f"   Uptime: {response.data.get('uptime', 'N/A')} ms")
            print(f"   Free Memory: {response.data.get('free_memory', 'N/A')} bytes")
            return True
        else:
            print("❌ Status test failed")
            return False
    
    def test_lighting(self) -> bool:
        print("\n=== Testing Lighting Command ===")
        
        response = self.send_command("lighting", {"channel": "led_1", "intensity": 128})
        if response and response.success:
            print("✅ LED 1 test passed")
        else:
            print("❌ LED 1 test failed")
            return False
        
        time.sleep(0.5)
        
        response = self.send_command("lighting", {"channel": "led_2", "intensity": 64})
        if response and response.success:
            print("✅ LED 2 test passed")
        else:
            print("❌ LED 2 test failed")
            return False
        
        time.sleep(0.5)
        
        response = self.send_command("lighting", {"channel": "all", "intensity": 0})
        if response and response.success:
            print("✅ All LEDs test passed")
            return True
        else:
            print("❌ All LEDs test failed")
            return False
    
    def test_photo_sequence(self) -> bool:
        print("\n=== Testing Photo Sequence Command ===")
        response = self.send_command("photo_sequence", {"count": 3, "delay": 0.5})
        if response and response.success:
            print("✅ Photo sequence test passed")
            return True
        else:
            print("❌ Photo sequence test failed")
            return False
    
    def run_all_tests(self) -> bool:
        print("Starting Arduino Communication Tests")
        print("=" * 40)
        
        tests = [
            self.test_ping,
            self.test_status,
            self.test_lighting,
            self.test_photo_sequence
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("\n" + "=" * 40)
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Arduino communication is working correctly.")
        else:
            print("⚠️  Some tests failed. Check Arduino connection and code.")
        
        return passed == total


def main():
    import sys
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        import platform
        if platform.system() == "Windows":
            port = "COM3"
        elif platform.system() == "Darwin":
            port = "/dev/tty.usbmodem*"
        else:
            port = "/dev/ttyUSB0"
        
        print(f"No port specified, using default: {port}")
        print("Usage: python test_arduino_communication.py <port>")
        print("Example: python test_arduino_communication.py COM3")
        print()
    
    tester = ArduinoTester(port)
    
    try:
        if tester.connect():
            tester.run_all_tests()
        else:
            print("Failed to connect to Arduino")
            print("\nTroubleshooting tips:")
            print("1. Make sure Arduino is connected via USB")
            print("2. Check if the correct port is being used")
            print("3. Ensure Arduino IDE Serial Monitor is closed")
            print("4. Verify ArduinoJson library is installed")
            print("5. Check if Arduino sketch is uploaded correctly")
    finally:
        tester.disconnect()


if __name__ == "__main__":
    main()

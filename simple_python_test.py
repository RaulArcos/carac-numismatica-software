#!/usr/bin/env python3
"""Simple Python script to test Arduino JSON communication."""

import serial
import json
import time
import sys

def test_arduino_communication():
    # Update this to your Arduino port
    port = "COM5"  # Change this if needed
    baud_rate = 9600
    timeout = 3.0
    
    print(f"Testing Arduino communication on {port} at {baud_rate} baud")
    print("=" * 50)
    
    try:
        # Open serial connection
        with serial.Serial(port, baud_rate, timeout=timeout, write_timeout=timeout) as ser:
            print("✓ Serial connection opened")
            
            # Wait a moment for Arduino to initialize
            time.sleep(2)
            
            # Read any initial messages
            print("\n--- Reading initial messages ---")
            for _ in range(3):  # Try reading a few times
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print(f"Arduino: {response}")
                        # Try to parse as JSON
                        try:
                            parsed = json.loads(response)
                            print(f"✓ Valid JSON: {parsed}")
                        except json.JSONDecodeError:
                            print(f"⚠ Not JSON: {response}")
                time.sleep(0.5)
            
            # Test sending commands
            print("\n--- Testing commands ---")
            
            test_commands = [
                {"type": "ping"},
                {"type": "test", "data": {"value": 123}},
                {"type": "led_toggle", "data": {"toggle": True}},
                "invalid json",  # Test error handling
            ]
            
            for i, cmd in enumerate(test_commands, 1):
                print(f"\nTest {i}:")
                if isinstance(cmd, dict):
                    cmd_str = json.dumps(cmd)
                    print(f"Sending JSON: {cmd_str}")
                else:
                    cmd_str = cmd
                    print(f"Sending text: {cmd_str}")
                
                # Send command
                ser.write((cmd_str + "\n").encode('utf-8'))
                ser.flush()
                
                # Wait for response
                start_time = time.time()
                received_responses = []
                
                while time.time() - start_time < 2.0:  # 2 second timeout per command
                    if ser.in_waiting > 0:
                        response = ser.readline().decode('utf-8').strip()
                        if response:
                            received_responses.append(response)
                            print(f"  Response: {response}")
                            
                            # Try to parse as JSON
                            try:
                                parsed = json.loads(response)
                                print(f"  ✓ Parsed JSON: {parsed}")
                            except json.JSONDecodeError:
                                print(f"  ⚠ Not JSON: {response}")
                    
                    time.sleep(0.1)
                
                if not received_responses:
                    print("  ✗ No response received")
                
                time.sleep(0.5)  # Small delay between tests
    
    except serial.SerialException as e:
        print(f"✗ Serial error: {e}")
        print("Make sure:")
        print("  1. Arduino is connected to the correct port")
        print("  2. Port is not being used by another application")
        print("  3. Arduino has the simple test sketch uploaded")
        return False
    
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("Test completed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow port to be specified as command line argument
        port = sys.argv[1]
        print(f"Using port: {port}")
    
    test_arduino_communication()

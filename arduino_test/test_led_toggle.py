#!/usr/bin/env python3
"""
Simple test script for LED toggle functionality
"""

import serial
import json
import time

def test_led_toggle():
    # Connect to Arduino
    try:
        print("Connecting to Arduino on COM3...")
        ser = serial.Serial('COM3', 9600, timeout=2)
        time.sleep(2)  # Wait for Arduino to reset
        
        print("Connected to Arduino")
        
        # Clear any pending data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Test ping first
        print("Testing ping...")
        ping_cmd = {"type": "ping"}
        ser.write((json.dumps(ping_cmd) + "\n").encode())
        response = ser.readline().decode().strip()
        print(f"Ping response: {response}")
        
        # Test LED toggle
        print("Testing LED toggle...")
        toggle_cmd = {"type": "led_toggle"}
        print(f"Sending toggle command: {toggle_cmd}")
        ser.write((json.dumps(toggle_cmd) + "\n").encode())
        
        # Read multiple lines to see all responses
        print("Reading responses:")
        for i in range(3):
            response = ser.readline().decode().strip()
            if response:
                print(f"  Line {i+1}: {response}")
            else:
                print(f"  Line {i+1}: (empty)")
        
        # Wait a moment
        time.sleep(1)
        
        # Test toggle again
        print("Sending toggle command again...")
        ser.write((json.dumps(toggle_cmd) + "\n").encode())
        
        response = ser.readline().decode().strip()
        print(f"Second toggle response: {response}")
        
        ser.close()
        print("Test completed")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_led_toggle()

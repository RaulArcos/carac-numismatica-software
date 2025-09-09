# Simple Arduino JSON Communication Test

This is a minimal test to verify basic JSON communication between Arduino and Python.

## Files Created

1. **`simple_arduino_test.ino`** - Minimal Arduino sketch
2. **`simple_python_test.py`** - Python test script
3. **`README_SIMPLE_TEST.md`** - This file

## How to Test

### Step 1: Upload Arduino Sketch
1. Open `simple_arduino_test.ino` in Arduino IDE
2. Select your Arduino Leonardo board and correct port (COM5)
3. Upload the sketch
4. Open Serial Monitor to verify it's working (should see "ready" message)

### Step 2: Run Python Test
```bash
python simple_python_test.py
```

Or specify a different port:
```bash
python simple_python_test.py COM3
```

## What the Test Does

### Arduino Sketch:
- Sends a JSON ready message on startup
- Listens for any incoming data
- Echoes back what it received
- Tries to parse incoming data as JSON
- Sends success/error responses in JSON format

### Python Script:
- Connects to Arduino
- Reads initial messages
- Sends various test commands (JSON and invalid)
- Displays all responses
- Shows which responses are valid JSON

## Expected Output

If working correctly, you should see:
- Initial ready message from Arduino
- Responses to each test command
- JSON parsing success/failure indicators

## Troubleshooting

If the test fails:
1. **Check port** - Make sure COM5 is correct
2. **Check connections** - Arduino should be properly connected
3. **Check Arduino IDE** - Verify sketch uploaded successfully
4. **Close other programs** - Make sure no other software is using the serial port
5. **Try different baud rate** - Some setups need different speeds

## Next Steps

- If this simple test works ✅ → The issue is in the complex code
- If this simple test fails ❌ → There's a fundamental communication problem

## Arduino Leonardo Specific Notes

Arduino Leonardo uses native USB serial, which can have timing issues:
- Longer delays may be needed
- Connection stability can vary
- Sometimes requires reset after upload

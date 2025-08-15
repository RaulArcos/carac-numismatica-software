# Arduino Test Software for Carac Numismatica

This Arduino sketch provides a simple test environment to verify serial communication with the desktop application.

## Requirements

- Arduino board (Uno, Nano, Mega, etc.)
- ArduinoJson library (version 6.x)
- 2 LEDs with resistors (optional, for testing lighting commands)
- USB cable for serial communication

## Installation

1. **Install ArduinoJson Library:**
   - Open Arduino IDE
   - Go to Tools → Manage Libraries
   - Search for "ArduinoJson" by Benoit Blanchon
   - Install version 6.x

2. **Upload the Sketch:**
   - Open `arduino_test.ino` in Arduino IDE
   - Select your Arduino board and port
   - Click Upload

## Hardware Setup (Optional)

For full testing functionality, connect:
- LED 1 to pin 9 (PWM)
- LED 2 to pin 10 (PWM)
- Built-in LED on pin 13 will be used for status indicators

## Communication Protocol

The Arduino expects JSON commands and responds with JSON responses:

### Command Format
```json
{
  "type": "command_type",
  "data": {...},
  "timestamp": 1234567890.123
}
```

### Response Format
```json
{
  "success": true/false,
  "message": "response message",
  "data": {...},
  "timestamp": 1234567890.123
}
```

## Supported Commands

### 1. Ping Command
Tests basic communication:
```json
{"type": "ping", "data": {"ping": true}, "timestamp": 1234567890.123}
```

**Response:**
```json
{"success": true, "message": "Pong!", "data": {"ping": true}, "timestamp": 123.456}
```

### 2. Status Command
Requests current Arduino status:
```json
{"type": "status", "data": {"status": true}, "timestamp": 1234567890.123}
```

**Response:**
```json
{
  "success": true,
  "message": "Status report",
  "data": {
    "uptime": 5000,
    "free_memory": 1024,
    "led_1_intensity": 128,
    "led_2_intensity": 0
  },
  "timestamp": 123.456
}
```

### 3. Lighting Command
Controls LED intensity:
```json
{
  "type": "lighting",
  "data": {
    "channel": "led_1",
    "intensity": 128
  },
  "timestamp": 1234567890.123
}
```

**Channels:**
- `"led_1"` - Controls LED on pin 9
- `"led_2"` - Controls LED on pin 10
- `"all"` - Controls both LEDs

**Intensity:** 0-255 (PWM value)

### 4. Photo Sequence Command
Simulates photo sequence:
```json
{
  "type": "photo_sequence",
  "data": {
    "count": 5,
    "delay": 1.0
  },
  "timestamp": 1234567890.123
}
```

## Testing with Serial Monitor

1. Open Arduino IDE Serial Monitor
2. Set baud rate to 9600
3. Set line ending to "Newline"
4. Send JSON commands

### Example Test Sequence

1. **Ping Test:**
   ```
   {"type": "ping", "data": {"ping": true}, "timestamp": 1234567890.123}
   ```

2. **Status Test:**
   ```
   {"type": "status", "data": {"status": true}, "timestamp": 1234567890.123}
   ```

3. **Lighting Test:**
   ```
   {"type": "lighting", "data": {"channel": "led_1", "intensity": 128}, "timestamp": 1234567890.123}
   ```

4. **Photo Sequence Test:**
   ```
   {"type": "photo_sequence", "data": {"count": 3, "delay": 0.5}, "timestamp": 1234567890.123}
   ```

## Features

- **JSON Parsing:** Uses ArduinoJson library for robust JSON handling
- **Error Handling:** Returns meaningful error messages for invalid commands
- **Status Monitoring:** Sends periodic status updates every 5 seconds
- **Visual Feedback:** Built-in LED blinks for activity indication
- **Memory Monitoring:** Reports free memory (where supported)

## Troubleshooting

1. **No Response:** Check baud rate (115200) and line ending (Newline)
2. **JSON Errors:** Ensure valid JSON format with proper quotes
3. **Memory Issues:** Some Arduino boards may not support freeMemory() function
4. **LED Not Working:** Check pin connections and resistor values

## Integration with Desktop App

This Arduino test software is designed to work with the Python desktop application. The communication protocol matches the models defined in `src/carac/protocol/models.py`.

When testing with the desktop app:
1. Upload this sketch to Arduino
2. Connect Arduino via USB
3. Use the desktop app's serial communication features
4. Monitor responses in both the desktop app and Arduino Serial Monitor

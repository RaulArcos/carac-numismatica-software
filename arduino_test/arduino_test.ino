#include <ArduinoJson.h>

const uint32_t BAUD_RATE = 9600;
const uint16_t BUFFER_SIZE = 300;
const uint32_t PING_INTERVAL = 10000;
const uint8_t LED_PIN = 13;  // Built-in LED on Arduino Leonardo

char inputBuffer[BUFFER_SIZE];
int bufferIndex = 0;
unsigned long lastPingTime = 0;
bool ledState = false;  // Track LED state

void processCommand(const char* jsonCommand);
void handlePingCommand();
void handleStatusCommand();
void handleMotorCommand(const JsonDocument& doc);
void handleLightingCommand(const JsonDocument& doc);
void handleWeightCommand(const JsonDocument& doc);
void handleSequenceCommand(const JsonDocument& doc);
void handleCalibrationCommand(const JsonDocument& doc);
void handleLedToggleCommand();
void handlePhotoSequenceCommand(const JsonDocument& doc);
void sendSimpleResponse(bool success, const String& message);
void sendResponse(bool success, const String& message, JsonObject data);
void sendStatusUpdate();
int getFreeMemory();

void setup() {
    Serial.begin(BAUD_RATE);
    
    // Initialize LED pin
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);  // Start with LED off
    ledState = false;
    
    while (!Serial) {
        ; // wait for serial port to connect. Needed for native USB
    }
    
    // Wait longer for serial to stabilize and Python to connect
    delay(1000);
    
    // Clear any data in the buffer
    while (Serial.available()) {
        Serial.read();
    }
    
    // Send initial ready response as JSON - using simple format
    sendSimpleResponse(true, "Ready");
    
    lastPingTime = millis();
}

void loop() {
    // Handle incoming serial data
    while (Serial.available()) {
        char c = Serial.read();
        
        if (c == '\n' || c == '\r') {
            if (bufferIndex > 0) {
                inputBuffer[bufferIndex] = '\0';
                processCommand(inputBuffer);
                bufferIndex = 0;
            }
        } else if (bufferIndex < BUFFER_SIZE - 1 && c >= 32 && c <= 126) {
            // Only accept printable ASCII characters
            inputBuffer[bufferIndex++] = c;
        } else if (bufferIndex >= BUFFER_SIZE - 1) {
            // Buffer overflow protection
            bufferIndex = 0;
            sendSimpleResponse(false, "Command too long");
        }
    }
    
    // No delay to ensure maximum responsiveness
}

void processCommand(const char* jsonCommand) {
    // Skip empty commands
    if (strlen(jsonCommand) == 0) {
        return;
    }
    
    StaticJsonDocument<BUFFER_SIZE> doc;
    DeserializationError error = deserializeJson(doc, jsonCommand);
    
    if (error) {
        String errorMsg = "JSON parsing error: ";
        errorMsg += error.c_str();
        sendSimpleResponse(false, errorMsg);
        return;
    }
    
    const char* commandType = doc["type"];
    if (!commandType) {
        sendSimpleResponse(false, "Missing command type");
        return;
    }
    
    String command = String(commandType);
    
    if (command == "ping") {
        handlePingCommand();
    } else if (command == "status") {
        handleStatusCommand();
    } else if (command == "motor") {
        handleMotorCommand(doc);
    } else if (command == "lighting") {
        handleLightingCommand(doc);
    } else if (command == "weight") {
        handleWeightCommand(doc);
    } else if (command == "sequence") {
        handleSequenceCommand(doc);
    } else if (command == "calibration") {
        handleCalibrationCommand(doc);
    } else if (command == "led_toggle") {
        handleLedToggleCommand();
    } else if (command == "photo_sequence") {
        handlePhotoSequenceCommand(doc);
    } else {
        sendSimpleResponse(false, "Unknown command: " + command);
    }
}

void handlePingCommand() {
    StaticJsonDocument<200> response;
    response["success"] = true;
    response["message"] = "Pong";
    response["timestamp"] = millis() / 1000.0;
    response["ping"] = true;
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    Serial.println(jsonResponse);
    Serial.flush();
}

void handleStatusCommand() {
    // Send minimal status to avoid memory issues
    int freeMem = getFreeMemory();
    float uptime = millis() / 1000.0;
    
    Serial.print("{\"success\":true,\"message\":\"Status\",\"data\":{\"free_memory\":");
    Serial.print(freeMem);
    Serial.print(",\"uptime\":");
    Serial.print(uptime);
    Serial.print(",\"led_state\":");
    Serial.print(ledState ? "true" : "false");
    Serial.println("}}");
    Serial.flush();
}

void handleLedToggleCommand() {
    // Toggle the LED state
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState ? HIGH : LOW);
    
    // Check memory before sending response
    int freeMem = getFreeMemory();
    if (freeMem < 100) {
        Serial.println("{\"success\":false,\"message\":\"Low memory\"}");
        Serial.flush();
        return;
    }
    
    // Send minimal response to avoid memory issues
    if (ledState) {
        Serial.println("{\"success\":true,\"message\":\"LED ON\",\"data\":{\"led_state\":true}}");
    } else {
        Serial.println("{\"success\":true,\"message\":\"LED OFF\",\"data\":{\"led_state\":false}}");
    }
    Serial.flush();
}

void handlePhotoSequenceCommand(const JsonDocument& doc) {
    // Minimal response to avoid buffer overflow
    Serial.println("{\"success\":true,\"message\":\"Photo OK\"}");
    Serial.flush();
}

void handleMotorCommand(const JsonDocument& doc) {
    JsonVariantConst dataVariant = doc["data"];
    if (dataVariant.isNull()) {
        sendSimpleResponse(false, "Missing data in motor command");
        return;
    }
    JsonObjectConst data = dataVariant.as<JsonObjectConst>();
    
    const char* action = data["action"];
    if (!action) {
        sendSimpleResponse(false, "Missing action in motor command");
        return;
    }
    
    StaticJsonDocument<256> response;
    response["success"] = true;
    response["timestamp"] = millis() / 1000.0;
    
    JsonObject responseData = response.createNestedObject("data");
    
    if (strcmp(action, "servo_left") == 0) {
        uint16_t position = data["position"].as<uint16_t>();
        if (position == 0) position = 710;
        response["message"] = "Servo left OK";
        responseData["servo"] = "left";
        responseData["position"] = position;
        responseData["simulated"] = true;
    } else if (strcmp(action, "servo_right") == 0) {
        uint16_t position = data["position"].as<uint16_t>();
        if (position == 0) position = 710;
        response["message"] = "Servo right OK";
        responseData["servo"] = "right";
        responseData["position"] = position;
        responseData["simulated"] = true;
    } else if (strcmp(action, "dc_left") == 0) {
        response["message"] = "DC left OK";
        responseData["motor"] = "dc";
        responseData["direction"] = "left";
        responseData["simulated"] = true;
    } else if (strcmp(action, "dc_right") == 0) {
        response["message"] = "DC right OK";
        responseData["motor"] = "dc";
        responseData["direction"] = "right";
        responseData["simulated"] = true;
    } else if (strcmp(action, "dc_stop") == 0) {
        response["message"] = "DC stop OK";
        responseData["motor"] = "dc";
        responseData["direction"] = "stop";
        responseData["simulated"] = true;
    } else {
        response["success"] = false;
        response["message"] = "Unknown motor action";
        responseData["action"] = action;
    }
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    Serial.println(jsonResponse);
    Serial.flush();
}

void handleLightingCommand(const JsonDocument& doc) {
    JsonVariantConst dataVariant = doc["data"];
    if (dataVariant.isNull()) {
        sendSimpleResponse(false, "Missing data in lighting command");
        return;
    }
    JsonObjectConst data = dataVariant.as<JsonObjectConst>();
    
    const char* channel = data["channel"];
    int intensity = data["intensity"].as<int>();
    
    if (!channel) {
        sendSimpleResponse(false, "Missing channel in lighting command");
        return;
    }
    
    StaticJsonDocument<256> response;
    response["success"] = true;
    response["message"] = "Lighting OK";
    response["timestamp"] = millis() / 1000.0;
    
    JsonObject responseData = response.createNestedObject("data");
    responseData["channel"] = channel;
    responseData["intensity"] = intensity;
    responseData["simulated"] = true;
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    Serial.println(jsonResponse);
    Serial.flush();
}

void handleWeightCommand(const JsonDocument& doc) {
    JsonVariantConst dataVariant = doc["data"];
    JsonObjectConst data = dataVariant.as<JsonObjectConst>();
    const char* action = data["action"];
    
    StaticJsonDocument<256> response;
    response["success"] = true;
    response["timestamp"] = millis() / 1000.0;
    
    JsonObject responseData = response.createNestedObject("data");
    
    if (!action || strcmp(action, "read") == 0) {
        uint8_t samples = data["samples"].as<uint8_t>();
        if (samples == 0) samples = 3;
        int32_t weightValue = random(-1000, 5000);
        response["message"] = "Weight OK";
        responseData["weight"] = weightValue;
        responseData["samples"] = samples;
        responseData["simulated"] = true;
    } else if (strcmp(action, "tare") == 0) {
        response["message"] = "Tare OK";
        responseData["tare_value"] = 0;
        responseData["simulated"] = true;
    } else {
        response["success"] = false;
        response["message"] = "Unknown weight action";
        responseData["action"] = action;
    }
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    Serial.println(jsonResponse);
    Serial.flush();
}

void handleSequenceCommand(const JsonDocument& doc) {
    JsonVariantConst dataVariant = doc["data"];
    if (dataVariant.isNull()) {
        sendSimpleResponse(false, "Missing data in sequence command");
        return;
    }
    JsonObjectConst data = dataVariant.as<JsonObjectConst>();
    
    uint8_t sequenceType = data["type"].as<uint8_t>();
    if (sequenceType == 0) sequenceType = 1;
    
    // Send start response
    StaticJsonDocument<256> response;
    response["success"] = true;
    response["message"] = "Sequence start";
    response["timestamp"] = millis() / 1000.0;
    
    JsonObject responseData = response.createNestedObject("data");
    responseData["sequence_type"] = sequenceType;
    responseData["simulated"] = true;
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    Serial.println(jsonResponse);
    Serial.flush();
    
    // Simulate sequence execution
    delay(100);
    
    // Send completion response
    response["message"] = "Sequence done";
    response["timestamp"] = millis() / 1000.0;
    
    String jsonResponseDone;
    serializeJson(response, jsonResponseDone);
    Serial.println(jsonResponseDone);
    Serial.flush();
}

void handleCalibrationCommand(const JsonDocument& doc) {
    JsonVariantConst dataVariant = doc["data"];
    if (dataVariant.isNull()) {
        sendSimpleResponse(false, "Missing data in calibration command");
        return;
    }
    JsonObjectConst data = dataVariant.as<JsonObjectConst>();
    
    const char* action = data["action"];
    if (!action) {
        sendSimpleResponse(false, "Missing action in calibration command");
        return;
    }
    
    StaticJsonDocument<256> response;
    response["success"] = true;
    response["timestamp"] = millis() / 1000.0;
    
    JsonObject responseData = response.createNestedObject("data");
    
    if (strcmp(action, "weight_tare") == 0) {
        response["message"] = "Cal OK";
        responseData["tare_value"] = 0;
        responseData["simulated"] = true;
    } else if (strcmp(action, "limit_switches") == 0) {
        response["message"] = "Switches OK";
        responseData["switch_1"] = false;
        responseData["switch_2"] = false;
        responseData["simulated"] = true;
    } else {
        response["success"] = false;
        response["message"] = "Unknown calibration action";
        responseData["action"] = action;
    }
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    Serial.println(jsonResponse);
    Serial.flush();
}

// Simple response function for basic messages
void sendSimpleResponse(bool success, const String& message) {
    // Create minimal JSON to avoid buffer overflow
    StaticJsonDocument<128> response;
    response["success"] = success;
    
    // Truncate message if too long
    String shortMessage = message;
    if (shortMessage.length() > 20) {
        shortMessage = shortMessage.substring(0, 20);
    }
    response["message"] = shortMessage;
    
    String jsonResponse;
    size_t len = serializeJson(response, jsonResponse);
    
    // Only send if response is reasonable size
    if (len > 0 && len < 100) {
        Serial.println(jsonResponse);
        Serial.flush();
    } else {
        // Fallback to hardcoded response
        if (success) {
            Serial.println("{\"success\":true,\"message\":\"OK\"}");
        } else {
            Serial.println("{\"success\":false,\"message\":\"Error\"}");
        }
        Serial.flush();
    }
}

void sendStatusUpdate() {
    StaticJsonDocument<300> response;
    response["success"] = true;
    response["message"] = "Status";
    response["timestamp"] = millis() / 1000.0;
    
    JsonObject responseData = response.createNestedObject("data");
    responseData["free_memory"] = getFreeMemory();
    responseData["uptime"] = millis() / 1000.0;
    responseData["platform"] = "Leonardo";
    responseData["type"] = "status_update";
    
    String jsonResponse;
    serializeJson(response, jsonResponse);
    Serial.println(jsonResponse);
    Serial.flush();
}

int getFreeMemory() {
    // Arduino Leonardo memory calculation
    extern int __heap_start, *__brkval;
    int v;
    return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

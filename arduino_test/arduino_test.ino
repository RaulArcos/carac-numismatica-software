#include <ArduinoJson.h>

const int LED_PIN = 13;  // Built-in LED for feedback
const int TEST_LED_1 = 9;
const int TEST_LED_2 = 10;
const int TEST_LED = 25;  // Using RX LED (pin 25) for toggle - this is an integrated LED on Leonardo

const unsigned long BAUD_RATE = 9600;
const int BUFFER_SIZE = 512;
char inputBuffer[BUFFER_SIZE];
int bufferIndex = 0;

unsigned long lastPingTime = 0;
const unsigned long PING_INTERVAL = 5000;

bool testLedState = false;  // Track the state of the test LED

void setup() {
  Serial.begin(BAUD_RATE);
  Serial.println("Arduino Test Software Started");
  Serial.println("Ready for JSON commands...");
  
  pinMode(LED_PIN, OUTPUT);
  pinMode(TEST_LED_1, OUTPUT);
  pinMode(TEST_LED_2, OUTPUT);
  pinMode(TEST_LED, OUTPUT);
  
  digitalWrite(LED_PIN, LOW);
  analogWrite(TEST_LED_1, 0);
  analogWrite(TEST_LED_2, 0);
  digitalWrite(TEST_LED, LOW);
  
  JsonObject initData = JsonObject();
  initData["status"] = "ready";
  sendResponse(true, "Arduino initialized and ready", initData);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    
    if (c == '\n') {
      inputBuffer[bufferIndex] = '\0';
      processCommand(inputBuffer);
      bufferIndex = 0;
    } else if (bufferIndex < BUFFER_SIZE - 1) {
      inputBuffer[bufferIndex++] = c;
    }
  }
  
  // Comment out periodic status updates for now to avoid interference
  // if (millis() - lastPingTime > PING_INTERVAL) {
  //   sendStatusUpdate();
  //   lastPingTime = millis();
  // }
}

void processCommand(const char* jsonCommand) {
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, jsonCommand);
  
  if (error) {
    JsonObject errorData = JsonObject();
    errorData["error"] = error.c_str();
    sendResponse(false, "JSON parsing error", errorData);
    return;
  }
  
  const char* commandType = doc["type"];
  if (!commandType) {
    sendResponse(false, "Missing command type", {});
    return;
  }
  
  if (strcmp(commandType, "ping") == 0) {
    handlePingCommand();
  } else if (strcmp(commandType, "status") == 0) {
    handleStatusCommand();
  } else if (strcmp(commandType, "lighting") == 0) {
    handleLightingCommand(doc);
  } else if (strcmp(commandType, "photo_sequence") == 0) {
    handlePhotoSequenceCommand(doc);
  } else if (strcmp(commandType, "led_toggle") == 0) {
    handleLedToggleCommand();
  } else {
    JsonObject errorData = JsonObject();
    errorData["received_type"] = commandType;
    sendResponse(false, "Unknown command type", errorData);
  }
}

void handlePingCommand() {
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);
  
  JsonObject pingData = JsonObject();
  pingData["ping"] = true;
  sendResponse(true, "Pong!", pingData);
}

void handleStatusCommand() {
  JsonObject data = JsonObject();
  data["uptime"] = millis();
  data["free_memory"] = freeMemory();
  data["led_1_intensity"] = analogRead(TEST_LED_1);
  data["led_2_intensity"] = analogRead(TEST_LED_2);
  data["test_led_state"] = testLedState;
  
  sendResponse(true, "Status report", data);
}

void handleLightingCommand(JsonDocument& doc) {
  JsonObject data = doc["data"];
  if (!data) {
    sendResponse(false, "Missing data in lighting command", {});
    return;
  }
  
  const char* channel = data["channel"];
  int intensity = data["intensity"] | 0;
  
  if (!channel) {
    sendResponse(false, "Missing channel in lighting command", {});
    return;
  }
  
  if (strcmp(channel, "led_1") == 0) {
    analogWrite(TEST_LED_1, intensity);
    JsonObject ledData = JsonObject();
    ledData["channel"] = "led_1";
    ledData["intensity"] = intensity;
    sendResponse(true, "LED 1 intensity set", ledData);
  } else if (strcmp(channel, "led_2") == 0) {
    analogWrite(TEST_LED_2, intensity);
    JsonObject ledData = JsonObject();
    ledData["channel"] = "led_2";
    ledData["intensity"] = intensity;
    sendResponse(true, "LED 2 intensity set", ledData);
  } else if (strcmp(channel, "all") == 0) {
    analogWrite(TEST_LED_1, intensity);
    analogWrite(TEST_LED_2, intensity);
    JsonObject ledData = JsonObject();
    ledData["channel"] = "all";
    ledData["intensity"] = intensity;
    sendResponse(true, "All LEDs intensity set", ledData);
  } else {
    JsonObject errorData = JsonObject();
    errorData["channel"] = channel;
    sendResponse(false, "Unknown lighting channel", errorData);
  }
}

void handlePhotoSequenceCommand(JsonDocument& doc) {
  JsonObject data = doc["data"];
  if (!data) {
    sendResponse(false, "Missing data in photo sequence command", {});
    return;
  }
  
  int count = data["count"] | 5;
  float delayTime = data["delay"] | 1.0;
  
  JsonObject startData = JsonObject();
  startData["count"] = count;
  startData["delay"] = delayTime;
  sendResponse(true, "Photo sequence started", startData);
  
  for (int i = 1; i <= count; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    
    JsonObject progressData = JsonObject();
    progressData["photo_number"] = i;
    progressData["total_photos"] = count;
    sendResponse(true, "Photo taken", progressData);
    
    if (i < count) {
      delay(delayTime * 1000);
    }
  }
  
  JsonObject completeData = JsonObject();
  completeData["photos_taken"] = count;
  sendResponse(true, "Photo sequence completed", completeData);
}

void handleLedToggleCommand() {
  // Step 1: Command received - flash LED once
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);
  
  // Step 2: Toggle the test LED state
  bool previousState = testLedState;
  testLedState = !testLedState;
  
  // Step 3: Set the test LED based on new state
  if (testLedState) {
    digitalWrite(TEST_LED, HIGH);  // Turn LED ON
  } else {
    digitalWrite(TEST_LED, LOW);   // Turn LED OFF
  }
  
  // Step 4: Visual feedback - different patterns for ON vs OFF
  if (testLedState) {
    // LED turned ON - flash twice quickly
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
  } else {
    // LED turned OFF - flash once slowly
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
  }
  
  // Step 5: Send JSON response with clear state information
  JsonObject ledData = JsonObject();
  ledData["state"] = testLedState;
  ledData["previous_state"] = previousState;
  ledData["action"] = testLedState ? "turned_on" : "turned_off";
  sendResponse(true, testLedState ? "LED turned ON" : "LED turned OFF", ledData);
}

void sendStatusUpdate() {
  JsonObject data = JsonObject();
  data["uptime"] = millis();
  data["free_memory"] = freeMemory();
  data["status"] = "idle";
  data["test_led_state"] = testLedState;
  
  sendResponse(true, "Periodic status update", data);
}

void sendResponse(bool success, const char* message, JsonObject data) {
  StaticJsonDocument<512> response;
  response["success"] = success;
  response["message"] = message;
  response["timestamp"] = millis() / 1000.0;
  
  if (!data.isNull()) {
    response["data"] = data;
  }
  
  String jsonResponse;
  serializeJson(response, jsonResponse);
  Serial.println(jsonResponse);
}

int freeMemory() {
  extern int __heap_start, *__brkval;
  int v;
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

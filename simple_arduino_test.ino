// Simple Arduino JSON communication test
#include <ArduinoJson.h>

void setup() {
    Serial.begin(9600);
    
    // Wait for serial port to connect
    while (!Serial) {
        ; 
    }
    
    delay(1000); // Give time for connection to stabilize
    
    // Send ready message
    Serial.println("{\"status\":\"ready\",\"message\":\"Simple test ready\"}");
    Serial.flush();
}

void loop() {
    // Check for incoming data
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        
        if (input.length() > 0) {
            // Echo back that we received something
            Serial.print("RECEIVED: ");
            Serial.println(input);
            Serial.flush();
            
            // Try to parse as JSON
            StaticJsonDocument<200> doc;
            DeserializationError error = deserializeJson(doc, input);
            
            if (error) {
                // Send error response
                Serial.println("{\"success\":false,\"message\":\"JSON parse error\"}");
            } else {
                // Send success response without echo to avoid JSON escaping issues
                Serial.println("{\"success\":true,\"message\":\"Command received\"}");
            }
            Serial.flush();
        }
    }
    
    delay(10); // Small delay to prevent overwhelming the serial
}

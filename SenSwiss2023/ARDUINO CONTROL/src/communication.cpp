#include "communication.h"
#include <Arduino.h>
#include "messages.h"

/*
* Initialize the serial port.
*/
void init_com() {
    Serial.begin(115200);
}

/*
* Read a message from the serial port.
* Returns an empty string if no message is available.
*/
String read_com() {
    if (Serial.available() > 0) {
        String message = "";
        while (Serial.available()) {
             message += (char)Serial.read();
        }
        return message;
    } else {
        return "";
    }
}

/*
* Send a message to the serial port.
*/
void write_com(String message) {
    Serial.print(message);
}
// Test code to communicate with the Leonardo's serial port
#include <Arduino.h>

#include "constantes.h"
#include "messages.h"
#include "communication.h"
#include "dc_motor.h"

// Static variables
static DCMotor motor;

void setup() {
  init_com();
  pinMode(PIN_LED, OUTPUT);

  motor = DCMotor(false, STATE_IDLE, DOWNWARD, 0.0);
  motor.initPins();

}

void loop() {

  // Check if a new command is received
  String message = read_com();
  if (message != "") {
    // Commands are separated by "-"
    int index = message.indexOf("-");
    String command = message.substring(0, index);
    String value = message.substring(index + 1);
    
    // Check if command is equal to a string inside MessageValueStrings
    int commandIndex = -1;
    for (int i = 0; i < NUMBER_OF_MESSAGES; i++) {
      if (command == MessageValueStrings[i]) {
        commandIndex = i;
        break;
      }
    }

    // If command is valid, execute it
    if (commandIndex != -1) {
      MessageValue messageValue = (MessageValue)commandIndex;
      switch (messageValue) {
        case DC_STOP:
          motor.setEnable(false);
          break;
        case DC_START:
          motor.setEnable(true);
          break;
        case DC_MOTOR_DIR:
          if (value == "0") {
            motor.setDirection(DOWNWARD);
          } else if (value == "1") {
            motor.setDirection(UPWARD);
          }
          break;
        case DC_MOTOR_SPEED:
          motor.setSpeed(value.toFloat());
          break;
        case OPEN_CHIP:
          motor.openChip();
          break;
        case CLOSE_CHIP:
          motor.closeChip();
          break;
      }
    }
  }

  motor.loop();
}
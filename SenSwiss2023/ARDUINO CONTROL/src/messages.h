/*
 * This file will contain all the string messages used to communicate between 
 * Guy (gui to control everything) and Leonardo (to control the motors)
 * 
 * These must match the strings in the python code (in /SenSwiss2023/guy/arduino_control.py)
 * All commands should be sent as follows : <command>-<value>
 * For example, to set the motor speed to 100, send the string "DC_MOTOR_SPEED-100"
 * <value> is optional for DC_START and DC_STOP
*/
#include <Arduino.h>

#ifndef MESSAGES_H
#define MESSAGES_H

enum MessageValue {
    DC_STOP,
    DC_START,
    DC_MOTOR_DIR,
    DC_MOTOR_SPEED,
    OPEN_CHIP,
    CLOSE_CHIP
};

#define NUMBER_OF_MESSAGES 6

#define ENUM_TO_STRING(enum) #enum
const String MessageValueStrings[] = {
    ENUM_TO_STRING(DC_STOP),
    ENUM_TO_STRING(DC_START),
    ENUM_TO_STRING(DC_MOTOR_DIR),
    ENUM_TO_STRING(DC_MOTOR_SPEED),
    ENUM_TO_STRING(OPEN_CHIP),
    ENUM_TO_STRING(CLOSE_CHIP)
};

#endif //MESSAGES_H
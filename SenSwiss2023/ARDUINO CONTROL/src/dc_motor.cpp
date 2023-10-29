#include "dc_motor.h"
#include <Arduino.h>
#include <ezButton.h>


#include "communication.h"

// Array used to average the current
static int currentArray[CURRENT_AVERAGE];
static int currentArrayIndex = 0;

DCMotor::DCMotor()
{
    this->_isEnable = false;
    this->_state = STATE_IDLE;
    this->_nextState = STATE_IDLE;
    this->_direction = DOWNWARD;
    this->_voltage = 0;
    this->_startingTime = 0;

}

DCMotor::DCMotor(bool isEnable, MotorControlState state, Direction direction, float voltage)
{
    this->_isEnable = isEnable;
    this->_state = state;
    this->_nextState = STATE_IDLE;
    this->_direction = direction;
    this->_voltage = voltage;
    this->_startingTime = 0;

}

DCMotor::~DCMotor()
{
}

void DCMotor::setEnable(bool isEnable)
{
    /*
        * Set enable of DC motor
        * 0: disable
        * 1: enable
    */
    if (isEnable) {
        if (this->_state == STATE_IDLE or this->_state == STATE_USER_CONTROL) { 
            this->_isEnable = true;
            this->_state = STARTING;
            this->_nextState = STATE_USER_CONTROL;
            this->_startingTime = millis();
        }
    } else {
        this->_isEnable = false;
        this->_state = STATE_IDLE;
        this->sendSignal();
    }
}

void DCMotor::setDirection(Direction direction)
{
    /*
        * Set direction of DC motor
        * 0: DOWNWARD
        * 1: UPWARD
    */
    if (this->_state == STATE_IDLE or this->_state == STATE_USER_CONTROL) { 
        this->_direction = direction;
    }
}

void DCMotor::setVoltage(float voltage)
{
    /*
        * Set voltage of DC motor, should be between 0 and 12V
    */
    if (this->_state == STATE_IDLE or this->_state == STATE_USER_CONTROL) { 
        if (voltage < 0) {
            voltage = 0;
        } else if (voltage > 12) {
            voltage = 12;
        }
        this->_voltage = voltage;
    }
}

bool DCMotor::getEnable()
{
    return this->_isEnable;
}

Direction DCMotor::getDirection()
{
    return this->_direction;
}

float DCMotor::getVoltage()
{
    return this->_voltage;
}

void DCMotor::setSpeed(float speed) {
    /*
    * Set speed of DC motor, should be between 0 and NOMINAL_SPEED (11 [rpm])
    */
    if (speed < 0) {
        speed = 0;
    } else if (speed > NOMINAL_SPEED) {
        speed = NOMINAL_SPEED;
    }
    // Converts the speed to voltage
    this->_voltage = SPEED_TO_VOLTAGE(speed);
}

void DCMotor::initPins() {
    /*
    * Initialize PINs for DC motor using PINs from constantes.h
    */
    pinMode(DC_MOTOR_DIRECTION_PIN, OUTPUT);
    pinMode(DC_MOTOR_BRAKE_PIN, OUTPUT);
    pinMode(DC_MOTOR_PWM_PIN, OUTPUT);
    pinMode(DC_MOTOR_CURRENT_PIN, INPUT);
}

void DCMotor::sendSignal() {
    /*
    * Send signals to DC motor using PINs from constantes.h
    */
    if (this->_isEnable) {
        if (this->_direction == DOWNWARD) {
            digitalWrite(DC_MOTOR_DIRECTION_PIN, LOW);
        } else {
            digitalWrite(DC_MOTOR_DIRECTION_PIN, HIGH);
        }
        digitalWrite(DC_MOTOR_BRAKE_PIN, LOW);
        analogWrite(DC_MOTOR_PWM_PIN, 255 * this->_voltage / 12);
    } else {
        digitalWrite(DC_MOTOR_DIRECTION_PIN, LOW);
        digitalWrite(DC_MOTOR_BRAKE_PIN, HIGH);
        analogWrite(DC_MOTOR_PWM_PIN, 0);
    }
}

void DCMotor::openChip() {
    /*
    * Open chip
    */

    this->_state = STARTING;
    this->_nextState = STATE_OPEN_CHIP;
    this->_startingTime = millis();

    this->_voltage = SPEED_TO_VOLTAGE(SPEED_DOWN);
    this->_direction = DOWNWARD;
    this->_isEnable = true;
}

void DCMotor::closeChip() {
    /*
    * Close chip
    */

    this->_state = STARTING;
    this->_nextState = STATE_CLOSE_CHIP;
    this->_startingTime = millis();

    this->_voltage = SPEED_TO_VOLTAGE(SPEED_UP);
    this->_direction = UPWARD;
    this->_isEnable = true;
}

int counter = 0;

void DCMotor::loop() {
    /*
    * Loop function for DC motor
    */

    // Average the current
    if (_state != STARTING && _state != STATE_IDLE) {
        currentArray[currentArrayIndex] = analogRead(DC_MOTOR_CURRENT_PIN);
        currentArrayIndex = (currentArrayIndex + 1) % CURRENT_AVERAGE;
    }
    int currentSum = 0;
    for (int i = 0; i < CURRENT_AVERAGE; i++) {
        currentSum += currentArray[i];
    }
    int current = currentSum / CURRENT_AVERAGE;
    
    if (_state != STARTING && current > MAX_CURRENT) {
        this->_isEnable = false;
        this->_voltage = 0;
        this->_state = STATE_IDLE;
        this->sendSignal();
    }
   
    switch (_state)
    {
    case STATE_IDLE:
        // Do nothing
        break;

    case STATE_USER_CONTROL:
        this->sendSignal();
        break;

    case STARTING:
        // Wait some time before setting limits on current
        if (millis() - this->_startingTime > STARTING_TIME) {
            for (int i = 0; i < CURRENT_AVERAGE; i++) {
                currentArray[i] = 0;
            }
            this->_state = this->_nextState;
        }
        this->sendSignal();
        break;

    case STATE_OPEN_CHIP:
        if (current > REF_CURRENT_DOWN) {
            this->_state = STATE_IDLE;
            this->_voltage = 0;
            this->_isEnable = false;

            for (int i = 0; i < CURRENT_AVERAGE; i++) {
                currentArray[i] = 0;
            }
        }
        this->sendSignal();
        break;

    case STATE_CLOSE_CHIP:
        if (current > REF_CURRENT_UP) {
            // We reached desired torque
            this->_voltage = 0;
            this->_isEnable = false;
            this->_state = STATE_IDLE;

            for (int i = 0; i < CURRENT_AVERAGE; i++) {
                currentArray[i] = 0;
            }
        }
        this->sendSignal();

        break;
    }
}


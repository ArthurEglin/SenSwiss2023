#ifndef DC_MOTOR_H_
#define DC_MOTOR_H_

#include <Arduino.h>
#include "constantes.h"

enum Direction
{
    DOWNWARD = 0,
    UPWARD = 1
};

enum MotorControlState
{
    STATE_IDLE,
    STATE_USER_CONTROL,
    STARTING,
    STATE_OPEN_CHIP,
    STATE_CLOSE_CHIP
};

class DCMotor
{
    private:
        bool _isEnable;
        MotorControlState _state;
        MotorControlState _nextState;

        // Directions given to shield
        Direction _direction;
        float _voltage;

        unsigned long _startingTime;

        // To close the chip
        float _integral;
        float _previousError;

    public:
        DCMotor();
        DCMotor(bool isEnable, MotorControlState state, Direction direction, float voltage);
        ~DCMotor();

        void setEnable(bool isEnable);
        void setDirection(Direction direction);
        void setVoltage(float voltage);

        bool getEnable();
        Direction getDirection();
        float getVoltage();

        void setSpeed(float speed);

        void initPins();
        void sendSignal();

        void openChip();
        void closeChip();

        void loop();
};

#endif /* DC_MOTOR_H_ */
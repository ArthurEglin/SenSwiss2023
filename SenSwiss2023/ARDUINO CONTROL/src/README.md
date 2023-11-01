# ARDUINO CONTROL

## Structure
The Arduino code is organized as follows:
- **communication.cpp** (+ **communication.h**): contains the functions to read and write on the serial USB port
- **constants.h**: contains the current and voltage control parameters as well as the PINs numbers of the Arduino Rev 3 Shield board used to control the motor (we use the motor port B)
- **dc_motor.cpp** (+ **dc_motor.h**): contains the functions to directly control the DC motor
- **main.cpp**: contains the main function for the motor control, it reads the commands sent by the GUI and calls the functions to control the motor
- **messages.h**: contains the different messages (string constants) corresponding to each motor action

## Installation, usage and code modification
In it state, the code is ready to be uploaded to the Arduino board, and is functional for the fonctionalities required by our prototype (open and close the measurement chamber).

To modify the code on the Arduino, you will need to install the Arduino IDE. You can download it [here](https://www.arduino.cc/en/software). Once the Arduino IDE is installed, you can open the code and upload it to the Arduino board. To do so, you will need to select the correct board and port in the Arduino IDE. You can find more information [here](https://www.arduino.cc/en/Guide/ArduinoLeonardoMicro#toc3).

## Description
We use the Arduino Leonardo as the motor controller along with Arduino Rev 3 Shield as the motor driver. The communication uses the RS232 protocol configured with a Baud rate of 115'200 bits/s, 8 data bits, 1 stop bit, no parity bit.

**dc_motor** is a class that allow to control the motor by PWM signal via the Arduino Rev 3 Shield. We send commands via the GUI to the Arduino board that creates the PWM signal for the motor. In the loop function we read the current value in real time (mean of the current value), to allow control of the torque and thus stop the motor when the torque is too high to impede damaging the measurement chamber and the chip. Since at the start, the current peaks to start the motor (high torque required), which would not be allowed by a simple current max threshold, we determined an empirical starting time of 300 ms to ignore this high current value, after this, the motor is stopped whenever the current passes 100 mA. The Arduino Shield Rev 3 is not very precise and sometimes detects very high values of current at random, this is why we use a mean value of the current.

## Authors
- [**Marin Bricq**](https://github.com/MBricq)
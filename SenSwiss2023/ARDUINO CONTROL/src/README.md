# ARDUINO CONTROL
We use the Arduino Leonardo as the motor controller along with Arduino Rev 3 Shield as a motor driver.

Communication uses RS232 protocol configured with a Beaud rate 115'200, 8 data bits, 1 stop bit, no parity bit.
The file contain two function to read and write on the serial USB port.

Constants.h
We use the motor port B. 

dc_motor is a class that allow to control the motor by PWM signal via the Arduino Rev 3 Shield. (signal carré qui varie en amplitude et en période). We send commands to the Rev 3 that creates the PWM signal for the motor.
in the loop function we read the current value in real time (mean of the current value), to allow to control the torque and thus stop the motor when the torque is too high. We can do this since DC motor do not have problem for the starting. At the start the current is high and then decrease when the motor is running, which could be a problem, this is why we determined a starting time to ignore this high current value.
voltage --> vitesse
courant --> torque
The Shield rev 3 is not very precise and sometimes detects very high values of current, which is why we use a mean value of the current to avoid this problem.


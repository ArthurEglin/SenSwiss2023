// Define the PINs of Leonardo board
#define PIN_LED 13
// Define the PINs of the DC motor shield
#define DC_MOTOR_PWM_PIN 11 // 3 for A
#define DC_MOTOR_DIRECTION_PIN 13 // 12 for A
#define DC_MOTOR_BRAKE_PIN 8 // 9 for A
#define DC_MOTOR_CURRENT_PIN A1 // A0 for A

// Define the DC motor electrical parameters
#define NOMINAL_CURRENT 0.69 // [A]
#define NOMINAL_VOLTAGE 12.0 // [V]
#define NOMINAL_SPEED 11.0 // [rpm]

#define SPEED_TO_VOLTAGE(n) (NOMINAL_VOLTAGE * n / NOMINAL_SPEED)

// Control parameters
#define MAX_CURRENT 100 // [mA]
#define REF_CURRENT_DOWN 70 // [mA]
#define REF_CURRENT_UP 75 // [mA]
#define CURRENT_AVERAGE 50 // [samples]
#define SPEED_UP 3.5 // [rpm/s]
#define SPEED_DOWN 3.5 // [rpm/s]
#define STARTING_TIME 300 // [ms]

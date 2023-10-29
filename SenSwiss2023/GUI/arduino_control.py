import serial
import serial.tools.list_ports

# Define the strings used to communicate with the arduino
# These must match the strings in the arduino code (in /SenSwiss2023/leonardo/messages.h)
# All commands should be sent as follows : <command>-<value>
# For example, to set the motor speed to 100, send the string "DC_MOTOR_SPEED-100"
# <value> is optional for DC_START and DC_STOP
DC_START = "DC_START"
DC_STOP = "DC_STOP"
DC_MOTOR_DIR = "DC_MOTOR_DIR"
DC_MOTOR_SPEED = "DC_MOTOR_SPEED"
OPEN_CHIP = "OPEN_CHIP"
CLOSE_CHIP = "CLOSE_CHIP"

def connect_arduino() -> (serial.Serial, bool):
    """
    Connect to the arduino and return the serial object and a boolean indicating whether the connection was successful
    """
    # Get the list of serial ports
    ports = list(serial.tools.list_ports.comports())
    # Find the port that has the arduino connected
    for port in ports:
        # Leonardo special number
        if (port.pid == 32822 and port.vid == 9025):
            # Create a serial object
            ser = serial.Serial(port.device, 115200, timeout=1)
            
            # Check if the arduino is connected
            if ser.is_open:
                # Return the serial object and a boolean indicating that the connection was successful
                print("Connected to arduino")
                return ser, True
            else:
                # Return the serial object and a boolean indicating that the connection was unsuccessful
                return ser, False
    # Return None and a boolean indicating that the connection was unsuccessful
    return None, False

def motor_powered(power_on: bool, ser: serial.Serial) -> bool:
    """
    Turn the motor on or off
    
    :param power_on: True to turn the motor on, False to turn it off
    :param ser: The serial object to use to communicate with the arduino
    
    :return: True if the command was sent successfully, False otherwise
    """
    try:
        message: str = ""
        if power_on:
            message = DC_START
        else:
            message = DC_STOP
        message += "-"
        ser.write(message.encode())
        return True
    except:
        print("Error writing to arduino")
        return False
    
def set_motor_speed(speed: float, ser: serial.Serial) -> bool:
    """
    Set the speed of the motor
    
    :param speed: The speed to set the motor to (0-100)
    :param ser: The serial object to use to communicate with the arduino
    
    :return: True if the command was sent successfully, False otherwise
    """
    try:
        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100
        message = DC_MOTOR_SPEED + "-" + str(speed)
        ser.write(message.encode())
        return True
    except:
        print("Error writing to arduino")
        return False
    
def set_motor_direction(direction: int, ser: serial.Serial) -> bool:
    """
    Set the direction of the motor
    
    :param direction: The direction to set the motor to (0=DOWN or 1=UP)
    :param ser: The serial object to use to communicate with the arduino
    
    :return: True if the command was sent successfully, False otherwise
    """
    try:
        if direction < 0:
            direction = 0
        elif direction > 1:
            direction = 1
        message = DC_MOTOR_DIR + "-" + str(direction)
        ser.write(message.encode())
        return True
    except:
        print("Error writing to arduino")
        return False
    
def open_chamber(ser: serial.Serial) -> bool:
    """
    Open the chamber
    
    :param ser: The serial object to use to communicate with the arduino
    
    :return: True if the command was sent successfully, False otherwise
    """
    try:
        message = OPEN_CHIP
        ser.write(message.encode())
        return True
    except:
        print("Error writing to arduino")
        return False
    
def close_chamber(ser: serial.Serial) -> bool:
    """
    Close the chamber
    
    :param ser: The serial object to use to communicate with the arduino
    
    :return: True if the command was sent successfully, False otherwise
    """
    try:
        message = CLOSE_CHIP
        ser.write(message.encode())
        return True
    except:
        print("Error writing to arduino")
        return False
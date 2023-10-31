# include python libraries
import time
import serial
import serial.tools.list_ports

pump_position: int = 0

######################## CONSTANTS #########################
# Sleep for the pump
wait_very_short: int = 10   # ms
wait_short: int = 100       # ms
wait_medium: int = 200      # ms
wait_long: int = 2000       # ms
wait_very_long: int = 5000  # ms
wait_forever: int = 120000  # ms

# Sleep for the GUI
sleep_short: float = 0.1    # s
sleep_long: float = 20      # s

# Pump parameters
max_position: int = 3000        # steps
volume_per_step: float = 83.3 # nL, working in normal resolution, Matilda: 83.3 nL, Matildina: 166.7 nL
# We noticed that the pump is not very accurate, so we need to calibrate it
# The volume is always 5% less than the expected volume
calibration_factor: float = 0.965


# Different valves, to be changed if we change the setup
trash_valve             : int = 1   # big tube
hcl_valve               : int = 2   # big tube
edc_nhs_valve           : int = 3   # big tube
bsa_valve               : int = 4   # big tube
ethanolamine_valve      : int = 5   # big tube
running_buffer_valve    : int = 6   # PBS: big
channel_1_valve         : int = 7   # small tube
channel_2_valve         : int = 8   # small tube
sample_valve            : int = 9   # small tube
antibody_valve          : int = 10   # small tube
# valve 11 is not used
# valve 12 is not used

# Some defined constants
big_tube_volume: int = 70       # uL
small_tube_volume: int = 35     # uL
trash_speed: int = 1000         # uL/min
pick_speed: int = 1000          # uL/min
disp_sample_speed: int = 20     # uL/min
disp_buffer_speed: int = 50     # uL/min

###################### BASE FUNCTIONS ######################

def connect_pump() -> (serial.Serial, bool):
    """
    Connects the pump to the computer.

    Returns:
        serial port of the pump, and a boolean that indicates if the pump is connected
    """
    try:
        ports = serial.tools.list_ports.comports(include_links=False)
        serial_port = ""
        for port in ports :
            if port.vid == 1027 and port.pid == 24597: # specific ID of Matilda
                serial_port = port.device
                break

        lsp: serial.Serial = serial.Serial(serial_port, 9600, timeout=1000)
        initialize_LSPOne(lsp)
        print("Pump connected")
        pump_connected = True
        return lsp, pump_connected
    except:
        print("Pump not connected")
        pump_connected: bool = False
        return None, pump_connected

def wait(time_in_ms: int) -> str:
    """
    Returns a string that represents a wait command for the pump.

    Args:
        time_in_ms: time to wait in milliseconds

    Returns:
        string that represents a wait command for the pump
    """
    output = "M" + str(time_in_ms)
    return output


# counter-clockwise rotation to the selected valve
def change_to_valve(valve_number: int) -> str:
    """
    Returns a string that represents a change valve command for the pump.

    Args:
        valve_number: number of the valve to change to

    Returns:    
        string that represents a change valve command for the pump
    """
    output = "O" + str(valve_number)
    return output


# clockwise rotation by valve_distance*60 degrees
def change_to_valve_relative(valve_distance: int) -> str:
    """
    Returns a string that represents a change valve relative command for the pump.
    
    Args:
        valve_distance: number of valves to rotate
        
    Returns:
        string that represents a change valve relative command for the pump
    """
    output = "I" + str(valve_distance)
    return output


def change_to_valve_fastest(valve_number: int) -> str:
    """
    Returns a string that represents a change valve command for the pump.
    This command is faster than change_to_valve.

    Args:
        valve_number: number of the valve to change to

    Returns:
        string that represents a change valve command for the pump
    """
    output = "B" + str(valve_number)
    return output


# position based on gear steps
def absolute_pump_position(step_position: int) -> str:
    """
    Returns a string that represents a go to absolute position command for the pump.
    Almost never used, because we use pickup_position and dispense_position.

    Args:
        step_position: position to go to, as to be between 0 and 3000, number of steps

    Returns:
        string that represents a go to absolute position command for the pump
    """

    global pump_position

    if step_position > max_position or step_position < 0:
        print("Volume is overshooting, you tried to go to: " + str(step_position))
        step_position = pump_position

    pump_position = step_position

    output = "A" + str(step_position)

    return output

def get_dispense_time(speed: float) -> float:
    """
    Get the time to dispense a certain volume at a certain speed.

    Args:
        speed (float): Speed of the pump, in uL/min.

    Returns:
        float: Time to dispense a certain volume at a certain speed, in ms.
    """
    diameter_of_tube = 0.42 # mm
    area_of_tube = 3.14 * (diameter_of_tube/2)**2 # mm^2
    length_of_tube = 200 # mm
    volume_of_tube = area_of_tube * length_of_tube # mm^3
    # With current tubing: 27.7 uL of tubing
    time = volume_of_tube / speed * 60 # s
    return time


# position based on gear steps
def pickup_position(pickup_distance: int) -> str:
    """
    Pickup a certain amount of steps.
    If we keep normal resolution, one step is 83.3 nL.

    Args:
        pickup_distance: number of steps to pickup, max 3000

    Returns:
        string that represents a pickup command for the pump
    """

    global pump_position

    old_position = pump_position

    pump_position = pump_position + pickup_distance

    if pump_position > max_position:
        print("Volume is overshooting, you tried to go to: " + str(pump_position))
        pickup_distance = max_position - old_position
        pump_position = max_position

    output = "P" + str(pickup_distance)

    return output


# position based on gear steps
def dispense_position(dispense_distance: int) -> str:
    """
    Dispense a certain amount of steps.
    If we keep normal resolution, one step is 83.3 nL.

    Args:
        dispense_distance: number of steps to dispense, min 0

    Returns:
        string that represents a dispense command for the pump
    """
    global pump_position

    old_position = pump_position

    pump_position = pump_position - dispense_distance

    if pump_position < 0:
        print("Volume is overshooting, you tried to go to: " + str(pump_position))
        dispense_distance = old_position
        pump_position = 0

    output = "D" + str(dispense_distance)

    return output

def seq_from_command(port: int, action: str, volume: float, speed: float, title: str, wait_t: int) -> str:
    """
    Returns a string that represents a sequence of commands for the pump.
    Go to the selected valve, pickup/dispense the selected volume at the selected speed.

    Args:
        port: port of the pump
        action: "Pick" or "Dispense"
        volume: volume to pickup/dispense, in uL (between 0 and 250)
        speed: speed of the pump, in uL/min

    Returns:
        string that represents a sequence of commands for the pump
    """

    to_ret = (change_to_valve_fastest(port)
            + wait(wait_medium)
            + peak_speed_uL_min(speed)
            + wait(wait_medium)
            + "?801")
    if action == "Pick":
        to_ret += pickup_uL(volume)
    elif action == "Dispense":
        to_ret += dispense_uL(volume)
    
    if wait_t > 0:
        to_ret += wait(wait_t)
    
    return to_ret

def peak_speed(pulse_per_sec: int) -> str:
    """
    Set speed of pump in pulses/sec.

    Args:
        pulse_per_sec (int or float): Min 1, Max 1600.

    Returns:
        string that represents a peak speed command for the pump
    """

    pulse_per_sec=round(pulse_per_sec)

    if(pulse_per_sec<1):
        print("Speed too low, setting to 1 pulses/sec")
        pulse_per_sec= 1

    if(pulse_per_sec>1600):
        print("Speed too high, setting to 1600 pulses/sec")
        pulse_per_sec=1600

    output = "V" + str(pulse_per_sec)
    return output

def peak_speed_uL_min(volume_per_min: float) -> str:
    """
    Set speed of pump in uL/min.
    
    Args:
        volume_per_min (float): Min 5, Max 8000. [uL/min]

    Returns:
        string that represents a peak speed command for the pump
    """

    step_per_sec = round(1/5 * volume_per_min) # For Matilda
    # step_per_sec = round(1/10 * volume_per_min) # For Matildina
    
    if(step_per_sec<1):
        print("Speed too low, setting to 1 pulses/sec")
        step_per_sec= 1
    elif(step_per_sec>1600):
        print("Speed too high, setting to 1600 pulses/sec")
        step_per_sec=1600

    # From the AMF documentation:
    # Motor speed [pulse/sec] = 1/5 * Flow rate [uL/min]
    # Min: 1 pulse/sec, Max: 1600 pulse/sec
    # => Min: 5 uL/sec, Max: 8000 uL/sec
    return peak_speed(step_per_sec)


# repeat sequence n times
def repeat_sequence(sequence: str, n: int) -> str:
    """
    Repeat a sequence n times.

    Args:
        sequence (str): Sequence to repeat.
        n (int): Number of times to repeat the sequence.

    Returns:
        string that represents a repeated sequence of commands for the pump
    """
    output = "g" + sequence + "G" + str(n)
    return output


def repeat_last_command() -> str:
    """
    Repeat the last command sent to the pump.

    Returns:
        string to send to the pump to repeat the last command
    """
    return "X"


def write_sequence_to_pump(lsp: serial.Serial, sequence: str) -> bool:
    """
    Write a sequence to the pump by appending a carriage return.

    Args:
        lsp (serial.Serial): Serial port to write to.
        sequence (str): Sequence to write to the pump.

    Returns:
        True if the sequence was written successfully, False otherwise.
    """

    output = "/1" + sequence + "R\r"

    try:
        lsp.write(output.encode())
        return True
    
    except:
        print("Error writing sequence to pump, check connection")
        return False


def set_force(lsp: serial.Serial, force: str) -> bool:
    """
    Set the force of the pump.

    Args:
        lsp (serial.Serial): Serial port to write to.
        force (str): Force to set the pump to. Can be "high", "normal", "medium" or "low". "medium" by default as
        it is indicated in the AMF documentation to either use "normal" or "medium" for 250 uL syringes.

    Returns:
        True if the force was set successfully, False otherwise.
    """

    forces = {
        "high": "/1Z0R\r",
        "normal": "/1Z1R\r",
        "medium": "/1Z2R\r",
        "low": "/1Z3R\r",
    }

    seq = forces.get(force, forces.get("medium"))

    try:
        lsp.write(seq.encode())
        time.sleep(sleep_long)
        print("Force set to " + force)
        return True
    except:
        print("Error writing sequence to pump, check connection")
        return False



def uL_volume_to_step(volume: float) -> int:
    """
    Convert a volume in uL to a number of steps.
    From the AMF documentation:
    1 step = 83.3 nL if we keep normal resolution. We added a calibration factor to account for the fact that the pump is not very precise.

    Args:
        volume (float): Volume in uL.
    
    Returns:
        int: Number of steps.
    """
    # Multiply by 1000 to get uL to nL
    return int(1000*volume/(volume_per_step*calibration_factor))


def absolute_position_uL(volume: float) -> str:
    """
    Return a sequence to go to a certain absolute position in uL.

    Args:
        volume (float): Volume in uL. Should be between 0 and 250.

    Returns:
        str: Sequence to send to the pump.
    """
    return absolute_pump_position(uL_volume_to_step(volume))


def pickup_uL(volume: float) -> str:
    """
    Return a sequence to pickup a certain volume in uL.

    Args:
        volume (float): Volume in uL. Should be between 0 and 250.

    Returns:
        str: Sequence to send to the pump.
    """

    return pickup_position(uL_volume_to_step(volume))


def dispense_uL(volume: float) -> str:
    """
    Return a sequence to dispense a certain volume in uL.

    Args:
        volume (float): Volume in uL. Should be between 0 and 250.

    Returns:
        str: Sequence to send to the pump.
    """
    return dispense_position(uL_volume_to_step(volume))

def initialize_LSPOne(lsp: serial.Serial) -> bool:
    """
    Initialize the LSP-One pump.

    Args:
        lsp (serial.Serial): Serial port to write to.

    Returns:
        True if the pump was initialized successfully, False otherwise.
    """
    success = set_force(lsp, "medium")
    if success:
        # Set pump in asynchronous mode
        lsp.write("/1!501\r".encode())
        print("LSPOne initialized")

    return success


def halt(lsp: serial.Serial) -> bool:
    """
    Stop the pump.

    Args:
        lsp (serial.Serial): Serial port to write to.

    Returns:
        True if the pump was stopped successfully, False otherwise.
    """
    seq = "/1T\r"
    
    try:
        lsp.write(seq.encode())
        return True
    except:
        print("Error writing sequence to pump, check connection")
        return False
    

def get_heat_seq(temp: float = 37.5) -> str:
    """
    Get the heating sequence for the LSP-One pump.

    Args:
        temp (float): Temperature to heat to. Defaults to 37.5.

    Returns:
        str: Sequence to send to the pump.
    """
    output = "@INCUB=" + str(10*float(temp))
    return output

def go_to_zero(lsp: serial.Serial) -> bool:
    """
    Go to position 0.

    Args:
        lsp (serial.Serial): Serial port to write to.

    Returns:
        True if the pump went to position 0 successfully, False otherwise.
    """
    final_sequence = (
        peak_speed(1000)
        + wait(wait_medium)
        + change_to_valve_fastest(trash_valve)
        + wait(wait_medium)
        + absolute_pump_position(0)
        + wait(wait_medium)
    )
    success1 = halt(lsp)
    time.sleep(sleep_short)
    success2 = write_sequence_to_pump(lsp, final_sequence) 
    return success1 and success2

def get_fill_seq() -> str:
    """
    Fill the tubes with the correct contents to remove air bubbles.

    Returns:
        str: Sequence to send to the pump.
    """

    seq = ""
    # First pick up big_tube_volume from each buffer channel (2, 3, 7, 8 and 12) at 50 uL/min. 
    # For PBS (7) do it last and do 200 uL
    # Each time dispense it into the waste channel (1) at trash_speed
    # Fill tube 2
    seq += seq_from_command(edc_nhs_valve, "Pick", big_tube_volume, pick_speed)
    # Trash
    seq += seq_from_command(trash_valve, "Dispense", big_tube_volume, trash_speed)
    # Fill tube 3
    seq += seq_from_command(bsa_valve, "Pick", big_tube_volume, pick_speed)
    # Trash
    seq += seq_from_command(trash_valve, "Dispense", big_tube_volume, trash_speed)
    # Fill tube 8
    seq += seq_from_command(ethanolamine_valve, "Pick", big_tube_volume, pick_speed)
    # Trash
    seq += seq_from_command(trash_valve, "Dispense", big_tube_volume, trash_speed)
    # Fill tube 12
    seq += seq_from_command(hcl_valve, "Pick", big_tube_volume, pick_speed)
    # Trash
    seq += seq_from_command(trash_valve, "Dispense", big_tube_volume, trash_speed)
    # Fill tube 7
    seq += seq_from_command(running_buffer_valve, "Pick", 200, pick_speed)
    # Trash
    seq += seq_from_command(trash_valve, "Dispense", 200, trash_speed)

    # Then pick up 4*small_tube_volume of PBS (7) at 50 uL/min and dispense small_tube_volule uL into valve 5 (channel 1) at 50 uL/min then
    # Same for valve 6 (channel 2)
    # Same for sample (valve 4) and antibodies (valve 9)
    # Fill syringe of PBS
    seq += seq_from_command(running_buffer_valve, "Pick", 4*small_tube_volume, pick_speed)
    # Dispense 30 uL into each valve
    seq += seq_from_command(channel_1_valve, "Dispense", small_tube_volume, disp_buffer_speed)
    seq += seq_from_command(channel_2_valve, "Dispense", small_tube_volume, disp_buffer_speed)
    seq += seq_from_command(sample_valve, "Dispense", small_tube_volume, disp_buffer_speed)
    seq += seq_from_command(antibody_valve, "Dispense", small_tube_volume, disp_buffer_speed)

    return seq

def get_functionalize_seq(use_channel_1: bool) -> str:
    """
    Functionalize the surface of the chip.

    Returns:
        str: Sequence to send to the pump.
    """
    seq = ""

    channel = channel_1_valve if use_channel_1 else channel_2_valve

    seq += seq_from_command(edc_nhs_valve, "Pick", 200, pick_speed)
    seq += seq_from_command(channel, "Dispense", 200, disp_buffer_speed)
    seq += seq_from_command(edc_nhs_valve, "Pick", 200, pick_speed)
    seq += seq_from_command(channel, "Dispense", 200, disp_buffer_speed)
    seq += seq_from_command(edc_nhs_valve, "Pick", 200, pick_speed)
    seq += seq_from_command(channel, "Dispense", 200, disp_buffer_speed)

    seq += seq_from_command(antibody_valve, "Pick", 200, 500)
    seq += seq_from_command(channel, "Dispense", 200, disp_sample_speed)
    seq += wait(30000)
    seq += seq_from_command(antibody_valve, "Pick", 200, 500)
    seq += seq_from_command(channel, "Dispense", 200, disp_sample_speed)

    return seq

def get_kick_bubble_seq(pick_channel: int, dispense_channel: int) -> str:
    """
    Kick the bubbles out of the tubes.

    Returns:
        str: Sequence to send to the pump.
    """
    seq = ""

    # check if the channel is valid (is between 1 and 12, and is an integer)
    try:
        if int(pick_channel) >= 1 and int(pick_channel) <= 12 and int(dispense_channel) >= 1 and int(dispense_channel) <= 12:
            seq += seq_from_command(pick_channel, "Pick", 200, 5000)
            seq += seq_from_command(dispense_channel, "Dispense", 50, 4000)
            seq += seq_from_command(dispense_channel, "Dispense", 50, 4000)
            seq += seq_from_command(dispense_channel, "Dispense", 100, 4000)
        else:
            print("Invalid channel number, please enter an integer between 1 and 12")
    except:
        print("Invalid channel number, please enter an integer between 1 and 12")
        
    return seq
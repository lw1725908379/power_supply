import time
import datetime
import logging

# Set up logging configuration, set log level to INFO, print errors to console
logging.basicConfig(level=logging.INFO)

def run_power_supply_operation(set_time, final_v=None, file_path=None, power=None):
    """
    Run power supply operations and record data.

    Args:
        set_time (int): Electrolysis time in seconds.
        final_v (float, optional): Final voltage value in volts. Defaults to None.
        file_path (str, optional): Local file path for storing data. Defaults to None.
        power (object, optional): Power supply object. Defaults to None.

    Returns:
        None
    """
    # Parameter type checks
    if not isinstance(set_time, int) or (final_v is not None and not isinstance(final_v, (int, float))):
        raise TypeError("set_time and final_v must be integers or floats.")
    if file_path is None:
        raise ValueError("File path for storing data must be provided.")
    if power is None:
        raise ValueError("Power supply object must be provided.")

    # Run set time and voltage operation
    set_time_and_voltage(set_time, final_v, file_path, power)


def set_time_and_voltage(set_time, final_v=None, file_path=None, power=None):
    """
    Set time and voltage, linearly increase or decrease voltage, perform electrolysis operation, and record voltage, current, and power to a local file.

    Args:
        set_time (int): Electrolysis time in seconds.
        final_v (float, optional): Final voltage value in volts. Defaults to None.
        file_path (str, optional): Local file path for storing data. Defaults to None.
        power (object, optional): Power supply object. Defaults to None.

    Returns:
        None
    """
    # Parameter type checks
    if not isinstance(set_time, int) or (final_v is not None and not isinstance(final_v, (int, float))):
        raise TypeError("set_time and final_v must be integers or floats.")
    if file_path is None:
        raise ValueError("File path for storing data must be provided.")
    if power is None:
        raise ValueError("Power supply object must be provided.")

    # Create file and write header
    with open(file_path, 'w') as f:
        f.write("Time,Voltage (V),Current (A),Power (W)\n")

    # Record start time
    start_time = time.time()

    # Set initial voltage
    init_v = power.V()

    # Calculate voltage change rate
    if final_v is not None:
        speed_v = (final_v - init_v) / set_time

    # Loop to run operation
    while time.time() - start_time < set_time:
        # Record current time
        current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        # Record current voltage, current, and power
        current_v = power.V()
        current_a = power.A()
        current_w = power.W()

        # Write data to file
        with open(file_path, 'a') as f:
            f.write(f"{current_time},{current_v},{current_a},{current_w}\n")

        # If final voltage is set, gradually adjust voltage
        if final_v is not None:
            power.set_volt(init_v + (time.time() - start_time) * speed_v)


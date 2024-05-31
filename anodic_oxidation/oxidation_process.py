import time
import logging
from tqdm import tqdm
from ..util.power_operations import run_power_supply_operation
from ..util.power_supply_tool import PowerSupply

def tiO2_nanotubes_anodic_oxidation(power: PowerSupply, file_path: str, time_per_iteration: int):
    """
    Perform anodic oxidation process for TiO2 nanotubes.

    Args:
        power (PowerSupply): Power supply object.
        file_path (str): Local file path for storing data.
        time_per_iteration (int): Duration of each iteration.

    Returns:
        None
    """
    # Set initial voltage of the power supply to zero
    power.set_voltage(0)

    # Logger
    logger = logging.getLogger(__name__)

    try:
        # Get user input settings
        num_stages = int(input("Enter the number of stages: "))
        # Loop through each stage
        for stage in range(1, num_stages + 1):
            logger.info("Starting Stage %d...", stage)
            # Get user input settings
            set_time_input = input("Enter the duration of Stage %d (seconds): " % stage)
            final_v_input = input("Enter the final voltage of Stage %d (V): " % stage)
            set_time = int(set_time_input) if set_time_input.strip() != "" else 500
            # If final_v is not provided, default to constant voltage
            final_v = float(final_v_input) if final_v_input.strip() != "" else None
            # Start timer
            start_time = time.perf_counter()
            # Run current stage with progress bar
            total_iterations = int(set_time / time_per_iteration)
            for _ in tqdm(range(total_iterations), desc="Stage %d" % stage):
                run_power_supply_operation(set_time=time_per_iteration, final_v=final_v, file_path=file_path, power=power)
            logger.info("Stage %d completed...", stage)
            # Log end time and current voltage, current, and power
            end_time = time.perf_counter()
            logger.info("Total program runtime: %s seconds", end_time - start_time)
            logger.info("Current displayed voltage: %s", power.get_voltage())
            logger.info("Current displayed current: %s", power.get_current())
            logger.info("Current displayed power: %s", power.get_power())
    except Exception as e:
        logger.error("An error occurred during execution:", exc_info=True)

    # Disconnect serial communication
    logger.info("Disconnecting serial communication...")
    power.set_operative_mode(0)
    # Reset voltage to zero
    power.set_voltage(0)

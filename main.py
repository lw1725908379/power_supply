from util.power_supply_tool import PowerSupplyTool
from anodic_oxidation.oxidation_process import tiO2_nanotubes_anodic_oxidation

def main():
    # Get user input for serial keyword, baud rate, and device address
    keyword = input("Enter the serial keyword: ")
    baud_rate = int(input("Enter the baud rate: "))
    addr = int(input("Enter the device address: "))

    # Create a PowerSupplyTool instance
    power_supply = PowerSupplyTool(keyword=keyword, baud_rate=baud_rate, addr=addr)

    # Get user input for file path and time per iteration
    file_path = input("Enter the local file path for storing data: ")
    time_per_iteration = int(input("Enter the time per iteration (in seconds): "))

    # Call the tiO2_nanotubes_anodic_oxidation function
    tiO2_nanotubes_anodic_oxidation(power=power_supply, file_path=file_path, time_per_iteration=time_per_iteration)

if __name__ == "__main__":
    main()


# Power Supply Project

This project provides a tool for controlling a power supply device and performing anodic oxidation processes for TiO2 nanotubes.

## Prerequisites

- Python 3.x
- Required Python packages: `pyserial`, `modbus-tk`, `tqdm`

## Installation

1. Clone this repository to your local machine:

    ```
    git clone https://github.com/your_username/power_supply.git
    ```

2. Install the required Python packages using pip:

    ```
    pip install -r requirements.txt
    ```

## Usage

1. Navigate to the project directory:

    ```
    cd power_supply
    ```

2. Run the `main.py` script:

    ```
    python main.py
    ```

3. Follow the on-screen prompts to enter the serial keyword, baud rate, device address, file path, and time per iteration.

4. The program will initialize the power supply and run the anodic oxidation process based on the provided inputs.

5. Once the process is complete, the program will disconnect the serial communication and reset the voltage to zero.

## Notes

- Make sure to connect the power supply device to the appropriate serial port before running the program.
- Ensure that the serial keyword, baud rate, and device address match the configuration of your power supply device.
- The program will create a local file to store the data collected during the anodic oxidation process.

## Author

- [wenLiu](https://github.com/lw1725908379)

## License

This project is licensed under the [MIT License](LICENSE).

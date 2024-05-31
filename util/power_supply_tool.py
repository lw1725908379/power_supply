import time
import serial
import serial.tools.list_ports
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import logging

# Set up logging configuration, set log level to INFO, print errors to console
logging.basicConfig(level=logging.INFO)


class PowerSupplyTool:
    """
    Author: wenLiu
    Created: 2022/10/25 22:45
    Power tool class, used to encapsulate the communication and control methods with power devices.
        read() :Read registers
        write(): Write data
        read_protection_state(): Read protection status
        V(): Read displayed voltage or write target voltage
        A(): Read displayed current or write limited current
        W(): Read displayed power
        OVP(): Read or write overvoltage protection set value
        OCP(): Read or write overcurrent protection set value
        OPP(): Read or write over power protection set value
        Addr(): Read or change slave address
        set_volt(): Set target voltage, wait for conversion and measure response time
        operative_mode(): Read or write working status
    """

    def __init__(self, keyword: str = "", baud_rate: int = 9600, timeout: int = 1, addr: int = 1):
        """
         Initialization method
         :param keyword: Keyword for serial port name
         :param baud_rate: Baud rate
         :param timeout: Serial port timeout
         :param addr: Device slave address
         """
        self.serial_obj = self.connect_serial(keyword, baud_rate, timeout)
        self.power_supply = PowerSupply(self.serial_obj, addr)

    def connect_serial(self, keyword: str = "", baud_rate: int = None, timeout: int = 1):
        """
        Connect to serial port
        :param keyword: Keyword for serial port name
        :param baud_rate: Baud rate
        :param timeout: Timeout
        :return: Serial port class
        """
        serial_list = list(serial.tools.list_ports.comports())
        if not serial_list:
            raise ValueError("Can't find a serial port")

        if not keyword:
            print("找到如下串口：")
            for serial_port in serial_list:
                print("\t", str(serial_port))
            print("请输入要连接的串口关键词：")
            keyword = input()

        if not baud_rate:
            print("请输入使用的波特率：")
            baud_rate = input()
            try:
                baud_rate = int(baud_rate)
            except ValueError:
                baud_rate = 9600

        for serial_port in serial_list:
            if keyword.lower() in str(serial_port).lower():
                try:
                    serial_obj = serial.Serial(serial_port.name, baud_rate, timeout=timeout)
                    print(f"与 {serial_port} 建立连接！")
                    return serial_obj
                except serial.SerialException as e:
                    logging.error(f"无法连接到 {serial_port}: {e}")
                    raise
        raise ValueError("Can't find the serial port")

    def set_voltage(self, voltage: float, error_range: int = 0.05, timeout: int = 600):
        """
        Set power supply output voltage
        :param voltage: Target voltage, unit: volts
        :param error_range: Allowable error range
        :param timeout: Timeout
        """
        self.power_supply.set_volt(voltage, error_range, timeout)

    def get_voltage(self):
        """
        Get the current output voltage of the power supply
        :return: Current voltage
        """
        return self.power_supply.V()

    def set_current(self, current: float):
        """
        Set power supply output current
        :param current: Target current, unit: Ampere
        """
        self.power_supply.A(current)

    def get_current(self):
        """
        Get the current output current of the power supply
        :return: Current current
        """
        return self.power_supply.A()

    def get_power(self):
        """
        Get the current output power of the power supply
        :return: Current power
        """
        return self.power_supply.W()

    def set_protection(self, ovp: float = None, ocp: float = None, opp: float = None):
        """
        Set power supply protection parameters
        :param ovp: Overvoltage protection value
        :param ocp: Overcurrent protection value
        :param opp: Overpower protection value
        """
        if ovp is not None:
            self.power_supply.OVP(ovp)
        if ocp is not None:
            self.power_supply.OCP(ocp)
        if opp is not None:
            self.power_supply.OPP(opp)

    def get_protection_state(self):
        """
        Get power supply protection state
        :return: Protection state
        """
        return self.power_supply.read_protection_state()

    def set_operative_mode(self, mode: int):
        """
        Get the current operating mode of the power supply
        :param mode: Current operating mode，1: Enable output; 0: Disable output
        """
        self.power_supply.operative_mode(mode)

    def get_operative_mode(self):
        """
        Get the current working status of the power supply
        :return: Current working status
        """
        return self.power_supply.operative_mode()


class PowerSupply:
    """
    Power class, used to communicate and control power devices
    """
    TIMEOUT = 1.0

    def __init__(self, serial_obj: serial.Serial, addr: int):
        """
        Constructor
        :param serial_obj: Serial port class
        :param addr: Slave Address
        """
        self.modbus_rtu_obj = modbus_rtu.RtuMaster(serial_obj)
        self.modbus_rtu_obj.set_timeout(self.TIMEOUT)
        self.addr = addr
        self.name = self.read(0x0003)
        self.class_name = self.read(0x0004)

        dot_msg = self.read(0x0005)
        self.W_dot = 10 ** (dot_msg & 0x0F)
        dot_msg >>= 4
        self.A_dot = 10 ** (dot_msg & 0x0F)
        dot_msg >>= 4
        self.V_dot = 10 ** (dot_msg & 0x0F)

        protection_state_int = self.read_protection_state()
        self.isOVP = protection_state_int & 0x01
        self.isOCP = (protection_state_int & 0x02) >> 1
        self.isOPP = (protection_state_int & 0x04) >> 2
        self.isOTP = (protection_state_int & 0x08) >> 3
        self.isSCP = (protection_state_int & 0x10) >> 4

        self.V(0)

    def read(self, reg_addr: int, reg_len: int = 1):
        """
        Read Register
        :param reg_addr: Register Address
        :param reg_len: Number of registers，1~2
        :return: data
        """
        response = self.modbus_rtu_obj.execute(self.addr, cst.READ_HOLDING_REGISTERS, reg_addr, reg_len)
        if reg_len == 1:
            return response[0]
        elif reg_len == 2:
            return response[0] << 16 | response[1]

    def write(self, reg_addr: int, data: int, data_len: int = 1):
        """
        Write data and verify
        :param reg_addr: Register Address
        :param data: Data to be written
        :param data_len: Data length
        :return: Write Status
        """
        if data_len == 1:
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr, output_value=data)
        elif data_len == 2:
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr, output_value=data >> 16)
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr + 1, output_value=data & 0xFFFF)

        # Verify the write result
        return self.verify_write(reg_addr, data, data_len)

    def verify_write(self, reg_addr: int, data: int, data_len: int):
        """
        Verify written data
        :param reg_addr: Register Address
        :param data: Data written
        :param data_len: Data length
        :return: Is the write successful?
        """
        if data_len == 1:
            return self.read(reg_addr) == data
        elif data_len == 2:
            return self.read(reg_addr) == (data >> 16) and self.read(reg_addr + 1) == (data & 0xFFFF)

    def read_protection_state(self):
        """
        Read protection status
        :return: Protection status register original value
        """
        return self.read(0x0002)

    def V(self, V_input: float = None):
        """
        Read the displayed voltage or write the target voltage
        :param V_input: Voltage value, unit: Volt
        :return: Display voltage or target voltage
        """
        if V_input is None:
            return self.read(0x0010) / self.V_dot
        else:
            self.write(0x0030, int(V_input * self.V_dot + 0.5))

import time
import serial
import serial.tools.list_ports
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import logging

# 设置日志配置,将日志级别设为 INFO,控制台打印错误
logging.basicConfig(level=logging.INFO)


class PowerSupplyTool:
    """
    Author: 刘文
    Created: 2022/10/25 22:45
    电源工具类，用于封装与电源设备的通信和控制方法
    """

    def __init__(self, keyword: str = "", baud_rate: int = 9600, timeout: int = 1, addr: int = 1):
        """
        初始化方法
        :param keyword: 串口名关键词
        :param baud_rate: 波特率
        :param timeout: 串口超时时间
        :param addr: 设备从机地址
        """
        self.serial_obj = self.connect_serial(keyword, baud_rate, timeout)
        self.power_supply = PowerSupply(self.serial_obj, addr)

    def connect_serial(self, keyword: str = "", baud_rate: int = None, timeout: int = 1):
        """
        连接串口
        :param keyword: 串口名关键词
        :param baud_rate: 波特率
        :param timeout: 超时时间
        :return: 串口类
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
        设置电源输出电压
        :param voltage: 目标电压，单位：伏特
        :param error_range: 容许的误差范围
        :param timeout: 超时时间
        """
        self.power_supply.set_volt(voltage, error_range, timeout)

    def get_voltage(self):
        """
        获取电源当前输出电压
        :return: 当前电压
        """
        return self.power_supply.V()

    def set_current(self, current: float):
        """
        设置电源输出电流
        :param current: 目标电流，单位：安
        """
        self.power_supply.A(current)

    def get_current(self):
        """
        获取电源当前输出电流
        :return: 当前电流
        """
        return self.power_supply.A()

    def get_power(self):
        """
        获取电源当前输出功率
        :return: 当前功率
        """
        return self.power_supply.W()

    def set_protection(self, ovp: float = None, ocp: float = None, opp: float = None):
        """
        设置电源保护参数
        :param ovp: 过压保护值
        :param ocp: 过流保护值
        :param opp: 过功率保护值
        """
        if ovp is not None:
            self.power_supply.OVP(ovp)
        if ocp is not None:
            self.power_supply.OCP(ocp)
        if opp is not None:
            self.power_supply.OPP(opp)

    def get_protection_state(self):
        """
        获取电源保护状态
        :return: 保护状态
        """
        return self.power_supply.read_protection_state()

    def set_operative_mode(self, mode: int):
        """
        设置电源工作状态
        :param mode: 工作状态，1: 开启输出; 0: 关闭输出
        """
        self.power_supply.operative_mode(mode)

    def get_operative_mode(self):
        """
        获取电源当前工作状态
        :return: 当前工作状态
        """
        return self.power_supply.operative_mode()


class PowerSupply:
    """
    电源类，用于与电源设备通信和控制
    """
    TIMEOUT = 1.0

    def __init__(self, serial_obj: serial.Serial, addr: int):
        """
        构造函数
        :param serial_obj: 串口类
        :param addr: 从机地址
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
        读取寄存器
        :param reg_addr: 寄存器地址
        :param reg_len: 寄存器个数，1~2
        :return: 数据
        """
        response = self.modbus_rtu_obj.execute(self.addr, cst.READ_HOLDING_REGISTERS, reg_addr, reg_len)
        if reg_len == 1:
            return response[0]
        elif reg_len == 2:
            return response[0] << 16 | response[1]

    def write(self, reg_addr: int, data: int, data_len: int = 1):
        """
        写入数据并验证
        :param reg_addr: 寄存器地址
        :param data: 待写入的数据
        :param data_len: 数据长度
        :return: 写入状态
        """
        if data_len == 1:
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr, output_value=data)
        elif data_len == 2:
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr, output_value=data >> 16)
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr + 1, output_value=data & 0xFFFF)

        # 验证写入结果
        return self.verify_write(reg_addr, data, data_len)

    def verify_write(self, reg_addr: int, data: int, data_len: int):
        """
        验证写入数据
        :param reg_addr: 寄存器地址
        :param data: 写入的数据
        :param data_len: 数据长度
        :return: 是否写入成功
        """
        if data_len == 1:
            return self.read(reg_addr) == data
        elif data_len == 2:
            return self.read(reg_addr) == (data >> 16) and self.read(reg_addr + 1) == (data & 0xFFFF)

    def read_protection_state(self):
        """
        读取保护状态
        :return: 保护状态寄存器原始值
        """
        return self.read(0x0002)

    def V(self, V_input: float = None):
        """
        读取表显电压或写入目标电压
        :param V_input: 电压值，单位：伏特
        :return: 表显电压或目标电压
        """
        if V_input is None:
            return self.read(0x0010) / self.V_dot
        else:
            self.write(0x0030, int(V_input * self.V_dot + 0.5))

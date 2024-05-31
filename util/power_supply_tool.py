import time
import serial
import serial.tools.list_ports
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import logging

# ������־����,����־������Ϊ INFO,����̨��ӡ����
logging.basicConfig(level=logging.INFO)


class PowerSupplyTool:
    """
    Author: ����
    Created: 2022/10/25 22:45
    ��Դ�����࣬���ڷ�װ���Դ�豸��ͨ�źͿ��Ʒ���
    """

    def __init__(self, keyword: str = "", baud_rate: int = 9600, timeout: int = 1, addr: int = 1):
        """
        ��ʼ������
        :param keyword: �������ؼ���
        :param baud_rate: ������
        :param timeout: ���ڳ�ʱʱ��
        :param addr: �豸�ӻ���ַ
        """
        self.serial_obj = self.connect_serial(keyword, baud_rate, timeout)
        self.power_supply = PowerSupply(self.serial_obj, addr)

    def connect_serial(self, keyword: str = "", baud_rate: int = None, timeout: int = 1):
        """
        ���Ӵ���
        :param keyword: �������ؼ���
        :param baud_rate: ������
        :param timeout: ��ʱʱ��
        :return: ������
        """
        serial_list = list(serial.tools.list_ports.comports())
        if not serial_list:
            raise ValueError("Can't find a serial port")

        if not keyword:
            print("�ҵ����´��ڣ�")
            for serial_port in serial_list:
                print("\t", str(serial_port))
            print("������Ҫ���ӵĴ��ڹؼ��ʣ�")
            keyword = input()

        if not baud_rate:
            print("������ʹ�õĲ����ʣ�")
            baud_rate = input()
            try:
                baud_rate = int(baud_rate)
            except ValueError:
                baud_rate = 9600

        for serial_port in serial_list:
            if keyword.lower() in str(serial_port).lower():
                try:
                    serial_obj = serial.Serial(serial_port.name, baud_rate, timeout=timeout)
                    print(f"�� {serial_port} �������ӣ�")
                    return serial_obj
                except serial.SerialException as e:
                    logging.error(f"�޷����ӵ� {serial_port}: {e}")
                    raise
        raise ValueError("Can't find the serial port")

    def set_voltage(self, voltage: float, error_range: int = 0.05, timeout: int = 600):
        """
        ���õ�Դ�����ѹ
        :param voltage: Ŀ���ѹ����λ������
        :param error_range: �������Χ
        :param timeout: ��ʱʱ��
        """
        self.power_supply.set_volt(voltage, error_range, timeout)

    def get_voltage(self):
        """
        ��ȡ��Դ��ǰ�����ѹ
        :return: ��ǰ��ѹ
        """
        return self.power_supply.V()

    def set_current(self, current: float):
        """
        ���õ�Դ�������
        :param current: Ŀ���������λ����
        """
        self.power_supply.A(current)

    def get_current(self):
        """
        ��ȡ��Դ��ǰ�������
        :return: ��ǰ����
        """
        return self.power_supply.A()

    def get_power(self):
        """
        ��ȡ��Դ��ǰ�������
        :return: ��ǰ����
        """
        return self.power_supply.W()

    def set_protection(self, ovp: float = None, ocp: float = None, opp: float = None):
        """
        ���õ�Դ��������
        :param ovp: ��ѹ����ֵ
        :param ocp: ��������ֵ
        :param opp: �����ʱ���ֵ
        """
        if ovp is not None:
            self.power_supply.OVP(ovp)
        if ocp is not None:
            self.power_supply.OCP(ocp)
        if opp is not None:
            self.power_supply.OPP(opp)

    def get_protection_state(self):
        """
        ��ȡ��Դ����״̬
        :return: ����״̬
        """
        return self.power_supply.read_protection_state()

    def set_operative_mode(self, mode: int):
        """
        ���õ�Դ����״̬
        :param mode: ����״̬��1: �������; 0: �ر����
        """
        self.power_supply.operative_mode(mode)

    def get_operative_mode(self):
        """
        ��ȡ��Դ��ǰ����״̬
        :return: ��ǰ����״̬
        """
        return self.power_supply.operative_mode()


class PowerSupply:
    """
    ��Դ�࣬�������Դ�豸ͨ�źͿ���
    """
    TIMEOUT = 1.0

    def __init__(self, serial_obj: serial.Serial, addr: int):
        """
        ���캯��
        :param serial_obj: ������
        :param addr: �ӻ���ַ
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
        ��ȡ�Ĵ���
        :param reg_addr: �Ĵ�����ַ
        :param reg_len: �Ĵ���������1~2
        :return: ����
        """
        response = self.modbus_rtu_obj.execute(self.addr, cst.READ_HOLDING_REGISTERS, reg_addr, reg_len)
        if reg_len == 1:
            return response[0]
        elif reg_len == 2:
            return response[0] << 16 | response[1]

    def write(self, reg_addr: int, data: int, data_len: int = 1):
        """
        д�����ݲ���֤
        :param reg_addr: �Ĵ�����ַ
        :param data: ��д�������
        :param data_len: ���ݳ���
        :return: д��״̬
        """
        if data_len == 1:
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr, output_value=data)
        elif data_len == 2:
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr, output_value=data >> 16)
            self.modbus_rtu_obj.execute(self.addr, cst.WRITE_SINGLE_REGISTER, reg_addr + 1, output_value=data & 0xFFFF)

        # ��֤д����
        return self.verify_write(reg_addr, data, data_len)

    def verify_write(self, reg_addr: int, data: int, data_len: int):
        """
        ��֤д������
        :param reg_addr: �Ĵ�����ַ
        :param data: д�������
        :param data_len: ���ݳ���
        :return: �Ƿ�д��ɹ�
        """
        if data_len == 1:
            return self.read(reg_addr) == data
        elif data_len == 2:
            return self.read(reg_addr) == (data >> 16) and self.read(reg_addr + 1) == (data & 0xFFFF)

    def read_protection_state(self):
        """
        ��ȡ����״̬
        :return: ����״̬�Ĵ���ԭʼֵ
        """
        return self.read(0x0002)

    def V(self, V_input: float = None):
        """
        ��ȡ���Ե�ѹ��д��Ŀ���ѹ
        :param V_input: ��ѹֵ����λ������
        :return: ���Ե�ѹ��Ŀ���ѹ
        """
        if V_input is None:
            return self.read(0x0010) / self.V_dot
        else:
            self.write(0x0030, int(V_input * self.V_dot + 0.5))

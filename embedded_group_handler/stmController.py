import serial
import time


class stmController():
    def __init__(self,DEF):
        super().__init__()
        self.DEF = DEF
        self.ser = None

        # self.openSerial(ttyName)
        self.sync = 0x00
        self.cmd_list = []
        self.recv_data = []

    def is_connected(self):
        return self.ser.is_open

    def connect(self, _ttyName='CDM4', _buadrate=115200):
        ## Open serial port at “115200,8,N,1”, timeout=0.1:
        self.ttyName = _ttyName #'/dev/tty' + ttyName
        self.ser = serial.Serial(_ttyName, baudrate=_buadrate, timeout=0.1)
        # print('>>> self.is_connected() : ', self.is_connected())
        return self.is_connected()

    def disconnect(self):
        self.ser.close()  # close port
        self.is_connected()

    def uint16_t_to_uint8_t_high(self, data):
        data_HIGH = ((data & 0xFF00) >> 8)
        return data_HIGH

    def uint16_t_to_uint8_t_low(self, data):
        data_LOW = (data & 0x00FF)
        return data_LOW

    def gram_to_bytes(self, _list, _idx, data):
        for d in data:
            _list.insert(_idx, self.uint16_t_to_uint8_t_high(int(data[d] * 10)))
            _idx += 1
            _list.insert(_idx, self.uint16_t_to_uint8_t_low(int(data[d] * 10)))
            _idx += 1

    def sendSerial(self, cmd=0x01, machineID=0x01, par1=None, par2=None, par3=None, par4=None):
        try:
            DATA_IDX = 3

            cmd_list = [self.DEF.STM_PACKET_LIST['STX'],
                        self.sync,
                        cmd,
                        machineID,
                        self.DEF.STM_PACKET_LIST['ETX']
                        ]
            # print('>> cmd_list     : ', cmd_list)

            ## data parsing gramx10 => uint8_t x 2
            if (machineID == self.DEF.DEV_ID['POW'])\
                    and (cmd == self.DEF.CMD_LIST['test'] or
                         cmd == self.DEF.CMD_LIST['make_beverage'] or
                         cmd == self.DEF.CMD_LIST['clean']):
                if par1 != None:
                    self.gram_to_bytes(cmd_list, DATA_IDX, par1)

                    if par2 != None:
                        DATA_IDX += len(par1)*2
                        self.gram_to_bytes(cmd_list, DATA_IDX, par2)

            elif (machineID == self.DEF.DEV_ID['CUP'] or
                  machineID == self.DEF.DEV_ID['LID']) \
                    and (cmd == self.DEF.CMD_LIST['test'] or
                         cmd == self.DEF.CMD_LIST['rotate']):
                cmd_list.insert(DATA_IDX, par1)
                DATA_IDX += 1
                if par2 != None:
                    cmd_list.insert(DATA_IDX, par2)
                    DATA_IDX += 1
                    if par3 != None:
                        cmd_list.insert(DATA_IDX, par3)
                        DATA_IDX += 1
                        if par4 != None:
                            cmd_list.insert(DATA_IDX, par4)
                            DATA_IDX += 1
            # update len
            LEN = len(cmd_list) - 1
            cmd_list.insert(1, LEN)

            # calculate checksum
            CHK = 0
            for i in range(2, LEN):
                CHK ^= cmd_list[i]
            cmd_list.insert(LEN+2, CHK)

            # sync num update
            if self.sync == 0xff:
                self.sync = 0x00
            else:
                self.sync += 0x01

            ## send serial packet
            if (self.is_connected()):
                self.ser.write(bytes(cmd_list))

                recv_data = self.readSerial()
                self.cmd_list = cmd_list
                if not self.checkValidation(cmd_list, recv_data):
                    # print('send data(byte)    : ', bytes(cmd_list))
                    print('send data(int)     : ', cmd_list)
                    # print("len : ", len(cmd_list))
                    # print('recieved data(bytes): ', recv_data)
                    print('recieved data(int)  : ', list(recv_data))
                    # print("len : ", len(recv_data))
                    err = "STM-PC network issue!"
                    return err
                else:
                    return True

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("type err : ", type(err))
            return err
            raise

    def readSerial(self):
        recv_data = self.ser.read(1)

        if recv_data != b'':
            while True:
                read_tmp = self.ser.read(1)
                if read_tmp:
                    recv_data = recv_data + read_tmp
                else:
                    break
                    time.sleep(0.001)

            return recv_data

    def checkValidation(self, send_data, received_data):
        # 패킷손실과 같은 경우 False를 반환
        if received_data != None:
            if len(send_data) == len(received_data):
                if send_data[-1] == received_data[-1]:
                    return True
                else:
                    return False

            return False
        else:
            return False


if __name__ == "__main__":
    stmC = stmController()
    while True:
        stmC.sendSerial()
        stmC.readSerial()
        time.sleep(0.5)
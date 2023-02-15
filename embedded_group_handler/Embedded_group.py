from multiprocessing import Process
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json
import time
import threading
from stmController import stmController

class Embedded_group():
    def __init__(self, ttyName = 'COM4'):
        # init embedded device
        self.DEF = self.DEF()
        self.status = self.DEF.STATUS_LIST['OFF']
        self.value = ''
        self.code = ''
        self.msg = ''
        self.connection = self.DEF.CONNECTION_LIST['DISCONNECTED']

        self.ttyName = ttyName

        self.STM = stmController(self.DEF)

        # init queue
        self.queue = []

        # connect to broker
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("127.0.0.1")

    def on_connect(self, client, userdata, flags, rc):
        print("[embedded_group_handler] MQTT Connected with result code "+str(rc))
        self.client.subscribe("/XS001/EMBEDDED_GROUP")

    def on_message(self, client, userdata, msg):
        print("[embedded_group_handler] msg_receiver push:", json.loads(msg.payload))
        self.queue.append(json.loads(msg.payload))

    def msg_receiver(self):
        self.client.loop_forever()

    def msg_send(self,topic,dict):
        msgs = \
            [
                {
                    'topic': topic,
                    'payload': json.dumps(dict)
                }
            ]
        publish.multiple(msgs, hostname="127.0.0.1")

    ###############################################################
    class DEF():
        def __init__(self):
            self.CODE = 0
            self.MSG = 1
            self.VALUE = 2
            self.STATUS = 3

            self.TF_LIST = {'TRUE': 'TRUE', 'FALSE': 'FALSE'}
            self.CONNECTION_LIST = {'CONNECTED': 'CONNECTED', 'DISCONNECTED': 'DISCONNECTED'}
            self.STATUS_LIST = {'OFF': 'OFF',
                                'ON': 'ON',
                                'READY': 'READY',
                                'RUNNING': 'RUNNING',
                                'STOPPED': 'STOPPED',
                                'ERROR': 'ERROR',
                                'IS_BUSY': 'IS_BUSY',
                                'IS_IDLE': 'IS_IDLE'}

            self.DEV_ID = {'POW': 0x00,
                           'ICE': 0x01,
                           'CUP': 0x02,
                           'LID': 0x03,
                           'HOT': 0x04}

            self.CMD_LIST = {'get_status': 0x00,
                             'connect': 0x01,
                             'disconnect': 0x02,
                             'get_connection': 0x03,
                             'is_connected': 0x04,
                             'stop': 0x05,
                             'is_stop': 0x06,
                             'initialize': 0x07,
                             'is_ready': 0x08,
                             'test': 0x09,
                             'get_error': 0x0a,
                             'is_busy': 0x0b,
                             'is_idle': 0x0c,
                             'make_beverage': 0x0d,
                             'dispatch': 0x0d,
                             'clean': 0x0e,
                             'rotate': 0x0e,
                             'get_sensor': 0x0f}

            self.STM_PACKET_LIST = {'STX': 0x02,
                                    'ETX': 0x03,
                                    'ONE_QUATER': 0x00,
                                    'TWO_QUATERS': 0x01,
                                    'THREE_QUATERS': 0x02,
                                    'CLOCKWISE': 0x00,
                                    'COUNTERCLOCKWISE': 0x01}
def Embedded_group_handler():
    #init
    embedded_group = Embedded_group(ttyName='COM15')

    #init thread
    mr = threading.Thread(target=embedded_group.msg_receiver)
    mr.start()

    while True:
        time.sleep(0.1)
        if (len(embedded_group.queue) > 0):
            request = embedded_group.queue.pop()
            result = []

            ## 1. PROCESS CONNECTION CMD
            if (request["cmd"] == 'connect'):
                if(embedded_group.STM.connect(embedded_group.ttyName)):
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.TF_LIST['TRUE']]
                else:
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.TF_LIST['FALSE']]
            elif (request["cmd"] == 'disconnect'):
                if(embedded_group.STM.disconnect(embedded_group.ttyName)):
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.TF_LIST['TRUE']]
                else:
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.TF_LIST['FALSE']]
            elif (request["cmd"] == 'get_connection'):
                if(embedded_group.STM.is_connected(embedded_group.ttyName)):
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.CONNECTED]
                else:
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.DISCONNECTED]
            elif (request["cmd"] == 'is_connected'):
                if(embedded_group.STM.disconnect(embedded_group.ttyName)):
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.TF_LIST['TRUE']]
                else:
                    embedded_group.value = embedded_group.DEF.CONNECTION_LIST[embedded_group.DEF.TF_LIST['FALSE']]
            else:
                result = embedded_group.STM.sendSerial(cmd=embedded_group.DEF.CMD_LIST[request["cmd"]],
                                                      machineID=embedded_group.DEF.DEV_ID[request["dev"]],
                                                      par1=request["par1"],
                                                      par2=request["par2"],
                                                      par3=request["par3"],
                                                      par4=request["par4"])
                ## error
                if (result != True) or (result != False):
                    if str(result) == "'NoneType' object has no attribute 'is_open'":
                        embedded_group.code = 1801
                        embedded_group.msg = "SERIAL IS NOT OPENED"


            response = {
                'seq': request["seq"],
                'type': 'RESPONSE',
                'cmd': request["cmd"],
                'dev': request["dev"],
                'num': request["num"],
                'code': embedded_group.code,
                'msg': embedded_group.msg,
                'value': embedded_group.value,
                'status': embedded_group.status
            }
            embedded_group.msg_send('/XS001/SYSTEM', response)
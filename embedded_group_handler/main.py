from multiprocessing import Process
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import json
import time
import threading
from Embedded_group import Embedded_group_handler
import datetime

class System:
    def __init__(self):
        # init queue
        self.queue = []

        # connect to broker
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("127.0.0.1")

    def on_connect(self, client, userdata, flags, rc):
        print("[system] MQTT Connected with result code " + str(rc))
        self.client.subscribe("/XS001/SYSTEM")

    def on_message(self, client, userdata, msg):
        # print(msg.topic+" "+str(msg.payload))
        print("[system] msg_receiver push:", json.loads(msg.payload))
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

if __name__ == '__main__':

    system = System()

    mr = threading.Thread(target=system.msg_receiver)
    mr.start()

    #multiprocess
    embedded_group_handler = Process(target=Embedded_group_handler)
    embedded_group_handler.start()
    embedded_group_handler.join

    request_list=[]

    time.sleep(1)
    # 1)edit the request format to msg what you want to test  (line 61 - 69)
    ####################### system send message #############################

    request = {
        'seq': str(datetime.datetime.now()),
        'dev': 'POW',
        'num': '01',
        'cmd': 'test',
        'par1': {'WT01' : 0, 'WT02' : 0,'WT03' : 0,'WT04' : 0,'WT05' : 0},
        'par2': {'PD01' : 0, 'PD02' : 0,'PD03' : 0,'PD04' : 0,'PD05' : 0},
        'par3': '',
        'par4': ''
    }
    # system.msg_send('/XS001/EMBEDDED_GROUP', request)
    #######################################################################

    #######################################################################
    request = {
        'seq': str(datetime.datetime.now()),
        'dev': 'POW',
        'num': '01',
        'cmd': 'connect',
        'par1': '',
        'par2': '',
        'par3': '',
        'par4': ''
    }
    system.msg_send('/XS001/EMBEDDED_GROUP', request)
    #######################################################################
    while True:
        if (len(system.queue) > 0):
            system.queue.pop()
            request = {
                'seq': str(datetime.datetime.now()),
                'dev': 'POW',
                'num': '01',
                'cmd': 'test',
                'par1': {'WT01': 15.2, 'WT02': 260.3, 'WT03': 0, 'WT04': 0, 'WT05': 0},
                'par2': {'PD01': 60.0, 'PD02': 300.0, 'PD03': 0, 'PD04': 0, 'PD05': 0},
                'par3': '',
                'par4': ''
            }
            system.msg_send('/XS001/EMBEDDED_GROUP', request)

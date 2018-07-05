import logging
import multiprocessing
import time

import serial


#TODO keepalive i obsluga resetu


class SerialProcess(multiprocessing.Process):
    def __init__(self, messageQ, commandQ, config):
        self.logger = logging.getLogger('RFLinkGW.SerialProcessing')

        self.logger.info("Starting...")
        multiprocessing.Process.__init__(self)

        self.__messageQ = messageQ
        self.__commandQ = commandQ

        self.gatewayPort = config['rflink_tty_device']
        self.sp = serial.Serial()
        self.connect()

        self.processing_exception = config['rflink_direct_output_params']

        self.processing_signed = config['rflink_signed_output_params']

    def close(self):
        self.sp.close()
        self.logger.debug('Serial closed')

    def prepare_output(self, data_in):
        out = []
        data = data_in.decode("ascii").replace(";\r\n", "").split(";")
        self.logger.debug("Received message:%s" % (data))
        if len(data) > 3 and data[0] == '20':
            family = data[2]
            deviceId = data[3].split("=")[1]
            d = {}
            for t in data[4:]:
                token = t.split("=")
                d[token[0]] = token[1]
            for key in d:
                if key in self.processing_exception:
                    val = d[key]
                elif key in self.processing_signed:
                    if int(d[key], 16) & 0x8000:
                        val = float -( (int(d[key], 16) & 0x7FFF)) / 10
                    else:
                        val = float (int(d[key], 16)) / 10
                else:
                    val = float (int(d[key], 16)) / 10
                topic_out = "%s/%s/READ/%s" % (family, deviceId, key)
                data_out = {
                    'method': 'publish',
                    'topic': topic_out,
                    'family': family,
                    'deviceId': deviceId,
                    'param': key,
                    'payload': val,
                    'qos': 1,
                    'timestamp': time.time()
                }
                out = out + [data_out]
        return out

    def prepare_input(self, task):
        out_str =  '10;%s;%s;%s;%s;\n' % (task['family'], task['deviceId'], task['param'], task['payload'])
        self.logger.debug('Sending to serial:%s' % (out_str))
        return out_str

    def connect(self):
        self.logger.info('Connecting to serial')
        while not self.sp.isOpen():
            try:
                time.sleep(1)
                self.sp = serial.Serial(self.gatewayPort, 57600, timeout=1)
                self.logger.debug('Serial connected')
            except Exception as e:
                self.logger.error('Serial port is closed %s' % (e))

    def run(self):
        self.sp.flushInput()
        while True:
            try:
                if not self.__commandQ.empty():
                    task = self.__commandQ.get()
                    # send it to the serial device
                    self.sp.write(self.prepare_input(task).encode('ascii'))
            except Exception as e:
                self.logger.error("Send error:%s" % (format(e)))
            try:
                if (self.sp.inWaiting() > 0):
                    data = self.sp.readline()
                    task_list = self.prepare_output(data)
                    for task in task_list:
                        self.logger.debug("Sending to Q:%s" % (task))
                        self.__messageQ.put(task)
                else:
                    time.sleep(0.01)
            except Exception as e:
                self.logger.error('Receive error: %s' % (e))
                self.connect()

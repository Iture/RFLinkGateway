import logging
import multiprocessing
import time

import paho.mqtt.client as mqtt

def is_number(s) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

class MQTTClient(multiprocessing.Process):
    def __init__(self, messageQ, commandQ, config) -> None:
        self.logger = logging.getLogger('RFLinkGW.MQTTClient')
        self.logger.info("Starting...")
        self.config=config
        multiprocessing.Process.__init__(self)
        self.__messageQ = messageQ
        self.__commandQ = commandQ
        self.client_connected = False
        self.connect_retry_counter = 0
        self.mqttDataPrefix = self.config['mqtt_prefix']
        self.mqttDataFormat = self.config['mqtt_format']
        self._mqttConn = mqtt.Client(client_id='RFLinkGateway')
        self._mqttConn.username_pw_set(self.config['mqtt_user'], self.config['mqtt_password'])

        self._mqttConn.on_disconnect = self._on_disconnect
        self._mqttConn.on_publish = self._on_publish
        self._mqttConn.on_message = self._on_message
        self._mqttConn.on_connect = self._on_connect
        self.connect(self.config)
        

    def connect (self,config) -> None:
        try:
            self._mqttConn.connect(config['mqtt_host'], port=config['mqtt_port'], keepalive=120)
        except Exception as e:
            self.logger.error("problem with connect: %s" % e)
    def close(self) -> None:
        self.logger.info("Closing connection")
        self._mqttConn.disconnect()

    def _on_connect(self,client,userdata,flags,rc) -> None:
        self.client_connected = True
        self.connect_retry_counter = 0
        self.logger.info("Client connected")
        self._mqttConn.subscribe("%s/+/+/WRITE/+" % self.mqttDataPrefix)


    def _on_disconnect(self, client, userdata, rc) -> None:
        if rc != 0:
            self.logger.error("Unexpected disconnection.")
            self.client_connected = False
            self.connect(self.config)

    def _on_publish(self, client, userdata, mid) -> None:
        self.logger.debug("Message " + str(mid) + " published.")

    def _on_message(self, client, userdata, message) -> None:
        self.logger.debug("Message received: %s" % (message))

        data = message.topic.replace(self.config['mqtt_prefix'] + "/", "").split("/")
        data_out = {
            'method': 'subscribe',
            'topic': message.topic,
            'family': data[0],
            'deviceId': data[1],
            'param': data[3],
            'payload': message.payload.decode('ascii'),
            'qos': 1
        }
        self.__commandQ.put(data_out)

    def publish(self, task) -> None:
        topic = "%s/%s" % (self.config['mqtt_prefix'], task['topic'])
        if self.mqttDataFormat == 'json':
            if is_number(task['payload']):
                task['payload'] = '{"value": ' + str(task['payload']) + '}'
            else:
                task['payload'] = '{"value": "' + str(task['payload']) + '"}'
        try:
            result = self._mqttConn.publish(topic, payload=task['payload'])
            self.logger.debug('Sending message %s :%s, result:%s' % (result.mid, task, result.rc))
            if result.rc != 0:
                raise Exception("Send failed")
        except Exception as e:
            self.logger.error('Publish problem: %s' % (e))
            self.__messageQ.put(task)

    def run(self):
        while True:
            if self.client_connected == False:
                #TODO Add reconnection limit
                time.sleep (1+2*self.connect_retry_counter)
                self.logger.error('Reconnecting, try:%s' % (self.connect_retry_counter+1))
                self.connect(self.config)
                self.connect_retry_counter += 1    
            else:
                if not self.__messageQ.empty():
                    task = self.__messageQ.get()
                    if task['method'] == 'publish':
                        self.publish(task)
                else:
                    time.sleep(0.1)
            self._mqttConn.loop()

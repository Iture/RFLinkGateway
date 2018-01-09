import logging
import multiprocessing
import time

import paho.mqtt.client as mqtt


class MQTTClient(multiprocessing.Process):
    def __init__(self, messageQ, commandQ, config):
        self.logger = logging.getLogger('RFLinkGW.MQTTClient')
        self.logger.info("Starting...")

        multiprocessing.Process.__init__(self)
        self.__messageQ = messageQ
        self.__commandQ = commandQ

        self.mqttDataPrefix = config['mqtt_prefix']
        self._mqttConn = mqtt.Client(client_id='RFLinkGateway')
        self._mqttConn.connect(config['mqtt_host'], port=config['mqtt_port'], keepalive=120)
        self._mqttConn.on_disconnect = self._on_disconnect
        self._mqttConn.on_publish = self._on_publish
        self._mqttConn.on_message = self._on_message

    def close(self):
        self.logger.info("Closing connection")
        self._mqttConn.disconnect()

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.error("Unexpected disconnection.")
            self._mqttConn.reconnect()

    def _on_publish(self, client, userdata, mid):
        self.logger.debug("Message " + str(mid) + " published.")

    def _on_message(self, client, userdata, message):
        self.logger.debug("Message received: %s" % (message))

        data = message.topic.replace(self.mqttDataPrefix + "/", "").split("/")
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

    def publish(self, task):
        topic = "%s/%s" % (self.mqttDataPrefix, task['topic'])
        try:
            self._mqttConn.publish(topic, payload=task['payload'])
            self.logger.debug('Sending:%s' % (task))
        except Exception as e:
            self.logger.error('Publish problem: %s' % (e))
            self.__messageQ.put(task)

    def run(self):
        self._mqttConn.subscribe("%s/+/+/W/+" % self.mqttDataPrefix)
        while True:
            if not self.__messageQ.empty():
                task = self.__messageQ.get()
                if task['method'] == 'publish':
                    self.publish(task)
            else:
                time.sleep(0.01)
            self._mqttConn.loop()

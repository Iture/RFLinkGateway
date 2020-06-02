import json
import logging
import multiprocessing
import time

import tornado.gen
import tornado.ioloop
import tornado.websocket
from tornado.options import options

import MQTTClient
import SerialProcess

logger = logging.getLogger('RFLinkGW')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


def main():
    # messages read from device
    messageQ = multiprocessing.Queue()
    # messages written to device
    commandQ = multiprocessing.Queue()

    config = {}
    try:
        with open('config.json') as json_data:
            config = json.load(json_data)
    except Exception as e:
        logger.error("Config load failed")
        exit(1)

    sp = SerialProcess.SerialProcess(messageQ, commandQ, config)
    sp.daemon = True
    sp.start()

    mqtt = MQTTClient.MQTTClient(messageQ, commandQ, config)
    mqtt.daemon = True
    mqtt.start()

    # wait a second before sending first task
    time.sleep(1)
    options.parse_command_line()

    mainLoop = tornado.ioloop.IOLoop.instance()
    mainLoop.start()


if __name__ == "__main__":
    main()

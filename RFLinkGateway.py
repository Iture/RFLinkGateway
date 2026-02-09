import os
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

def load_config():
    # load config.json and overrides with environnment variables
    config = {}

    try:
        with open('config.json') as f:
            config = json.load(f)
        logger.info("Configuration loaded from config.json")
    except Exception as e:
        logger.error("Failed to load config.json: %s", e)
        exit(1)

    env = {k.lower(): v for k, v in os.environ.items()}
    for key in list(config.keys()):
        key_lower = key.lower()
        if key_lower in env:
            raw_value = env[key_lower]

            # parsing JSON (list, dict, bool, int…)
            try:
                value = json.loads(raw_value)
            except Exception:
                value = raw_value

            logger.info("Config override: %s = %s (env)", key, value)
            config[key] = value

    return config

def setup_logger(config):
    level_str = config.get("log_level", "DEBUG").upper()
    level = getattr(logging, level_str, logging.DEBUG)

    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(level)

    # remove previous handlers to avoid duplicates (if reload)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(ch)

def main():
    # load configuration
    config = load_config()
    setup_logger(config)
    logger.info("Starting RFLinkGateway with log_level=%s", config.get("log_level"))
    
    # messages read from device
    messageQ = multiprocessing.Queue()
    # messages written to device
    commandQ = multiprocessing.Queue()

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

#!/usr/bin/python3

import cv2
import yaml
import time
import datetime
import logging
import logging.handlers
import signal
import sys
import os

# Load config file
try:
    with open('/opencv_client/config.yaml', 'r') as f:
        options = yaml.load(f, Loader=yaml.SafeLoader)
except OSError as exception:
    print(exception)
    sys.exit()


# Set variables
logName = options["global"]["logfile"]
output_dir = options["global"]["output_dir"]
reconnect_time = options["global"]["reconnect_time"]
capture_duration = options["global"]["capture_duration"]

for item in options["devices"]["camera1"]:
    globals()[f"{item}"] = options["devices"]["camera1"][f"{item}"]

# Logging
rotateHandler = logging.handlers.RotatingFileHandler(logName, maxBytes=10485760, backupCount=5)
formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(message)s|','%d/%m/%Y %H:%M:%S')

logger = logging.getLogger('Logger')

logger.setLevel(logging.DEBUG)
rotateHandler.setFormatter(formatter)
logger.addHandler(rotateHandler)

logger.info('Program start')

# Check variables
if not os.path.exists(output_dir):
    print(output_dir, 'not exist')
    logger.warning('%s not exist', output_dir)
    logger.info('Graceful exit')
    sys.exit()

class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True

killer = GracefulKiller()

fourcc = cv2.VideoWriter_fourcc(*'XVID')

while not killer.kill_now:
    if reconnect_time > (options["global"]["reconnect_time"] * 10):
        reconnect_time = options["global"]["reconnect_time"] * 10
    try:
        logger.info('Trying to connect to %s:%s', ip_address, port)
        cap = cv2.VideoCapture(protocol + '://' + user + ':' + password + '@' + ip_address + ':' + port + '/' + path)
        if cap is None or not cap.isOpened():
            raise ConnectionError
        capStatus = True
        retTest, frameTest = cap.read()
        if not retTest:
            if capStatus:
                logger.warning('Unable to open camera')
                time.sleep(reconnect_time)
                capStatus = False
            continue
        else:
            if not capStatus:
                logger.info('Camera opened after awaiting!')
            logger.info('Camera connect success')

        now = datetime.datetime.now()
        start_time = int(time.time())
        fileName = output_dir + now.strftime('%Y_%m_%d_%H_%M_%S') + '.avi'
        out = cv2.VideoWriter(fileName,fourcc, 4.0, (1920,1080))
        logger.info('Record started')

        while( ( int(time.time() - start_time ) < capture_duration) and not killer.kill_now ):
            ret, frame = cap.read()
            if ret==True:
                out.write(frame)
            else:
                break

        out.release()
        logger.info('Record ended')
    except ConnectionError:
        print("Retrying connection to camera in ",str(reconnect_time), " seconds...")
        logger.warning('Connection error. Wait for reconnection.')
        time.sleep(reconnect_time)

    reconnect_time += reconnect_time

cap.release()

logger.info('Graceful exit')

import json
import os
from urllib.parse import urlparse

import Jetson.GPIO as GPIO
import paho.mqtt.client as mqtt

# configure logging
# get log level from environment variable
import logging as log
log_level = os.getenv('LOG_LEVEL', 'INFO')
log.basicConfig(
    level=getattr(log, log_level.upper(), log.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        log.StreamHandler()
    ]
)

# Get the configuration JSON from the environment variable
config_json = os.getenv('CONFIGURATION')

# Parse the JSON to extract the serial port device name
if config_json:
    config = json.loads(config_json)
else:
    raise ValueError("CONFIGURATION environment variable not set or is empty")

# GPIO and PWM configuration
neutral_position = int(config.get('neutral_position', 60))
max_right_position = int(config.get('max_right_position', 70))
max_left_position = int(config.get('max_left_position', 50))
pin = int(config.get('pin', 15))
frequency = int(config.get('frequency', 400))
topic = config.get('topic')


# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER')
parsed_url = urlparse(MQTT_BROKER)
MQTT_BROKER_HOST = parsed_url.hostname
MQTT_BROKER_PORT = int(parsed_url.port)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)
pwm = GPIO.PWM(pin, frequency)
pwm.start(neutral_position)


def set_signal(value):
    """
    signal is sent by neuron network or by desktop application, range 0..1, 0.5 is the middle
    """
    middle = 0.5
    delta = value - middle
    log.debug(f"delta: {delta}")
    if delta < 0:
        # go left
        dynamic_range = abs(neutral_position - max_left_position)
        duty_cycle = neutral_position - abs(delta) / middle * dynamic_range
        pwm.ChangeDutyCycle(duty_cycle)
        log.debug(f"going left, dynamic_range: {dynamic_range}, duty_cycle: {duty_cycle}")
    elif delta > 0:
        # go right
        dynamic_range = abs(neutral_position - max_right_position)
        duty_cycle = neutral_position + abs(delta) / middle * dynamic_range
        pwm.ChangeDutyCycle(duty_cycle)
        log.debug(f"going right, dynamic_range: {dynamic_range}, duty_cycle: {duty_cycle}")
    elif delta == 0:
        # go neutral
        pwm.ChangeDutyCycle(neutral_position)
        log.debug(f"going straight")


# MQTT event handlers
def on_connect(client, userdata, flags, rc):
    log.debug("MQTT connected with result code: " + str(rc))
    # Subscribe to a topic
    client.subscribe(topic)
    log.debug(f"MQTT subscribed to {topic}")


def on_message(client, userdata, msg):
    log.debug("Message received on topic " + msg.topic + ": " + str(msg.payload))

    if msg.topic == topic:
        value = float(msg.payload.decode())
        log.debug(f"signal: {value}")
        set_signal(value)
    else:
        log.debug("Unknown topic")


log.debug(f"MQTT connecting at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")

# MQTT client setup
client = mqtt.Client(reconnect_on_failure=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 30)

# Blocking call to process network traffic, dispatch callbacks, and handle reconnecting.
# It will run forever unless an exception occurs or a signal is sent to stop it.
try:
    client.loop_forever()
finally:
    pwm.stop()
    GPIO.cleanup()

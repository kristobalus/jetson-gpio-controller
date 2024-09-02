import json
import os
import time
from urllib.parse import urlparse

import Jetson.GPIO as GPIO
import paho.mqtt.client as mqtt

# Get the configuration JSON from the environment variable
config_json = os.getenv('CONFIGURATION')

# Parse the JSON to extract the serial port device name
if config_json:
    config = json.loads(config_json)
else:
    raise ValueError("CONFIGURATION environment variable not set or is empty")

# GPIO and PWM configuration
neutral_position = int(config.get('neutral_position', 60))
max_right = int(config.get('max_right', 70))
max_left = int(config.get('max_left', 50))
pin = int(config.get('pin', 15))
frequency = int(config.get('frequency', 400))

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER')
parsed_url = urlparse(MQTT_BROKER)
MQTT_BROKER_HOST = parsed_url.hostname
MQTT_BROKER_PORT = int(parsed_url.port)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pin, frequency)
pwm.start(neutral_position)


def neutral_to_left():
    for duty_cycle in range(neutral_position, max_right, 1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


def left_to_neutral():
    for duty_cycle in range(max_right, neutral_position, -1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


def neutral_to_right():
    for duty_cycle in range(neutral_position, max_left, -1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


def right_to_neutral():
    for duty_cycle in range(max_left, neutral_position, 1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


# MQTT event handlers
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribe to a topic
    client.subscribe("drive/command")


def on_message(client, userdata, msg):
    print("Message received on topic " + msg.topic + ": " + str(msg.payload))
    command = msg.payload.decode()

    if command == "neutral_to_left":
        neutral_to_left()
    elif command == "left_to_neutral":
        left_to_neutral()
    elif command == "neutral_to_right":
        neutral_to_right()
    elif command == "right_to_neutral":
        right_to_neutral()
    else:
        print("Unknown command")


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

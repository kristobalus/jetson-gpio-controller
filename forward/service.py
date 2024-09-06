import json
import os
import time
from urllib.parse import urlparse

import Jetson.GPIO as GPIO
import paho.mqtt.client as mqtt

# Get the configuration JSON from the environment variable
config_json = os.getenv("CONFIGURATION")

# Parse the JSON to extract the serial port device name
if config_json:
    config = json.loads(config_json)
else:
    raise ValueError("CONFIGURATION environment variable not set or is empty")

# GPIO and PWM configuration
full_forward = int(config.get("full_forward", 55))
full_backward = int(config.get("full_backward", 40))
full_stop = int(config.get("full_stop", 53))
topic = config.get('topic')

pin = int(config.get("pin", 32))
frequency = int(config.get("frequency", 400))

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")
parsed_url = urlparse(MQTT_BROKER)
MQTT_BROKER_HOST = parsed_url.hostname
MQTT_BROKER_PORT = int(parsed_url.port)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pin, frequency)
pwm.start(full_stop)

current_state = 0


def go_stop(interval):
    start_time = time.time()
    while time.time() - start_time < interval:
        pwm.ChangeDutyCycle(full_stop)


def go_forward(interval):
    start_time = time.time()
    while time.time() - start_time < interval:
        pwm.ChangeDutyCycle(full_forward)


def go_backward(interval):
    start_time = time.time()
    pwm.ChangeDutyCycle(full_backward)
    pwm.ChangeDutyCycle(full_stop)
    while time.time() - start_time < interval:
        pwm.ChangeDutyCycle(full_backward)


# MQTT event handlers
def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code " + str(rc))
    # Subscribe to a topic
    client.subscribe(topic)


def on_message(client, userdata, msg):
    print("MQTT message received on topic " + msg.topic + ": " + str(msg.payload))

    if msg.topic == topic:
        value = float(msg.payload.decode())
        print(f"signal: {value}")
        set_signal(value)
    else:
        print("Unknown topic")


def set_signal(value):
    """
    signal is sent by neuron network or by desktop application, range 0..1, 0.5 is the middle
    """
    global current_state
    print(f"current_state={current_state}")

    if value >= 0.51:
        # forward motion
        go_forward(1)
    elif value <= 0.49:
        # backward motion
        if current_state < 0.5:
            go_backward(1)
            go_forward(0.1)
            current_state = 0.5
        else:
            go_stop(0.1)
            go_backward(0.1)
            go_stop(0.1)
            go_backward(1)
            go_forward(0.1)
            current_state = 0.5
    elif value == 0.5:
        # brake
        go_stop(0.1)

    current_state = value


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

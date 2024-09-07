import json
import os
import threading
import time
from urllib.parse import urlparse
from threading import Thread

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

prev_value = 0.5
motion_interval = 10
motion_duty_cycle = full_stop
motion_time = 0
motion_time_lock = threading.Lock()  # Lock for thread-safe access
motion_duty_cycle_lock = threading.Lock()  # Lock for thread-safe access
motion_thread: Thread


def go_stop(duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        pwm.ChangeDutyCycle(full_stop)


def go_forward(duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        pwm.ChangeDutyCycle(full_forward)


def go_backward(duration):
    global motion_time
    start_time = time.time()
    while time.time() - start_time < duration:
        pwm.ChangeDutyCycle(full_backward)


def motion_thread_handler():
    start_time = time.time()
    while True:
        with motion_time_lock:
            current_motion_time = motion_time  # Safely read the global motion_time
        if time.time() - start_time >= current_motion_time:
            break
        pwm.ChangeDutyCycle(motion_duty_cycle)  # Simulate PWM action
        # time.sleep(0.001)  # prevent high CPU overusage


# Function to start go_forward in a thread
def start_motion_thread():
    global motion_thread
    global motion_time
    if motion_thread is None or motion_thread.is_alive() is False:
        motion_thread = Thread(target=motion_thread_handler)
        motion_thread.start()
    else:
        with motion_time_lock:
            motion_time = motion_time + motion_interval


def stop_motion_thread():
    global motion_time
    with motion_time_lock:
        motion_time = 0
    if motion_thread:
        motion_thread.join()


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
    global motion_time
    global prev_value
    global motion_duty_cycle
    if value > 0.5:

        if prev_value > 0.5:
            # keep motion
            start_motion_thread()

        if prev_value < 0.5:
            stop_motion_thread()
            go_forward(0.1)
            with motion_duty_cycle_lock:
                motion_duty_cycle = full_forward
            with motion_time_lock:
                motion_time = motion_interval

        if prev_value == 0.5:
            with motion_duty_cycle_lock:
                motion_duty_cycle = full_forward
            with motion_time_lock:
                motion_time = motion_interval
            start_motion_thread()

    if value == 0.5:
        if prev_value < 0.5:
            stop_motion_thread()
            go_forward(0.1)
            with motion_duty_cycle_lock:
                motion_duty_cycle = full_stop
            with motion_time_lock:
                motion_time = motion_interval
            start_motion_thread()
        if prev_value > 0.5:
            stop_motion_thread()
            with motion_duty_cycle_lock:
                motion_duty_cycle = full_stop
            with motion_time_lock:
                motion_time = motion_interval
            start_motion_thread()

    if value < 0.5:
        # backward motion
        if prev_value < 0.5:
            start_motion_thread()
        if prev_value == 0.5 or prev_value > 0.5:
            stop_motion_thread()
            go_stop(0.1)
            go_backward(0.1)
            go_stop(0.1)
            with motion_duty_cycle_lock:
                motion_duty_cycle = full_backward
            with motion_time_lock:
                motion_time = motion_interval
            start_motion_thread()

    prev_value = value


# MQTT client setup
client = mqtt.Client(reconnect_on_failure=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 30)

try:
    client.loop_forever()
finally:
    pwm.stop()
    GPIO.cleanup()

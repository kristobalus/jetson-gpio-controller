import json
import os
import threading
import time
from urllib.parse import urlparse
from threading import Thread
from typing import Optional
import paho.mqtt.client as mqtt
import math
from unittest.mock import MagicMock
import logging as log
import signal
import sys


def graceful_shutdown(signal_number, frame):
    print("Shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGTERM, graceful_shutdown)


# configure logging
# get log level from environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO')
log.basicConfig(
    level=getattr(log, log_level.upper(), log.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        log.StreamHandler()
    ]
)

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
use_dynamic_range = bool(config.get('use_dynamic_range', False))
use_fake_device = bool(config.get('use_fake_device', False))
topic = config.get('topic')

log.info("configuration %s", {"config": config})

if topic is None:
    raise Exception("Should have topic defined")

log.debug(f"Use dynamic range: {use_dynamic_range}")

pin = int(config.get("pin", 32))
frequency = int(config.get("frequency", 400))

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")
parsed_url = urlparse(MQTT_BROKER)
MQTT_BROKER_HOST = parsed_url.hostname
MQTT_BROKER_PORT = int(parsed_url.port)

if use_fake_device:
    def on_side_effect(duty_cycle):
        log.debug(f"Fake PWM: duty cycle applied={duty_cycle}")
    pwm = MagicMock()
    pwm.ChangeDutyCycle = MagicMock(side_effect=on_side_effect)
else:
    import Jetson.GPIO as GPIO

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pin, GPIO.OUT)

    pwm = GPIO.PWM(pin, frequency)
    pwm.start(full_stop)

prev_value = 0.5
motion_interval = int(config.get("motion_interval", 10))
motion_duty_cycle = full_stop
motion_time = 0
motion_time_lock = threading.Lock()  # Lock for thread-safe access
motion_duty_cycle_lock = threading.Lock()  # Lock for thread-safe access
prev_value_lock = threading.Lock()  # Lock for thread-safe access
motion_thread: Optional[Thread] = None


def go_stop(duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        pwm.ChangeDutyCycle(full_stop)
    log.debug(f"go_stop completed for {duration} sec")


def go_forward(duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        pwm.ChangeDutyCycle(full_forward)
    log.debug(f"go_forward completed for {duration} secs")


def go_backward(duration):
    global motion_time
    start_time = time.time()
    while time.time() - start_time < duration:
        pwm.ChangeDutyCycle(full_backward)
    log.debug(f"go_backward completed for {duration} secs")


def motion_thread_handler():
    log.debug(f"thread start")
    start_time = time.time()
    global prev_value
    while True:
        with motion_duty_cycle_lock:
            current_duty_cycle = motion_duty_cycle  # Safely read the global motion_time
        with motion_time_lock:
            current_motion_time = motion_time  # Safely read the global motion_time
        if time.time() - start_time >= current_motion_time:
            break
        pwm.ChangeDutyCycle(current_duty_cycle)  # Simulate PWM action
        time.sleep(0.001)  # prevent high CPU overusage
    log.debug(f"motion loop timeout")
    if motion_duty_cycle < full_stop:
        log.debug(f"prevent PWM controller locking")
        go_forward(0.1)
        go_stop(0.1)
    if motion_duty_cycle > full_stop:
        go_stop(0.1)
    with prev_value_lock:
        prev_value = full_stop
    log.debug(f"now full stop")
    log.debug(f"thread end")


# Function to start go_forward in a thread
def start_motion_thread():
    global motion_thread
    global motion_time
    if motion_thread and motion_thread.is_alive():
        with motion_time_lock:
            motion_time = motion_time + motion_interval
        log.debug(f"motion time extended {motion_time}")
    else:
        with motion_time_lock:
            motion_time = motion_interval
        motion_thread = Thread(target=motion_thread_handler)
        motion_thread.start()
        log.debug(f"motion thread started")


def stop_motion_thread():
    global motion_time
    if motion_thread and motion_thread.is_alive():
        with motion_time_lock:
            motion_time = 0
        motion_thread.join()
        log.debug(f"motion thread stopped")


# MQTT event handlers
def on_connect(client, userdata, flags, rc):
    log.info("MQTT connected with result code " + str(rc))
    # Subscribe to a topic
    client.subscribe(topic)
    log.info(f"MQTT subscribed to {topic}")


def on_message(client, userdata, msg):
    log.debug("MQTT message received on topic " + msg.topic + ": " + str(msg.payload.decode()))

    if msg.topic == topic:
        try:
            arr = json.loads(msg.payload.decode())
            log.debug("MQTT control signal received %s", arr)
            apply_control_signal(arr[0])
        except Exception as e:
            log.error(e)
    else:
        log.debug(f"Unknown topic: {msg.topic}")


def dynamic_range_forward(value):
    if use_dynamic_range is False:
        return full_forward
    if value == 0.5:
        raise Exception(f"Value should not be equal to full_stop: {value}")
    range_ratio = abs(value - 0.5) / 0.5
    dynamic_range = abs(full_forward - full_stop)
    delta = range_ratio * dynamic_range
    result = full_stop + delta
    result = min(math.ceil(result), full_forward)
    log.debug(f"dynamic_range: {dynamic_range}, range_ratio={range_ratio}, result={result}")
    return result


def dynamic_range_backward(value):
    if use_dynamic_range is False:
        return full_backward
    if value == 0.5:
        raise Exception(f"Value should not be equal to full_stop: {value}")
    range_ratio = abs(value - 0.5) / 0.5
    dynamic_range = abs(full_backward - full_stop)
    delta = range_ratio * dynamic_range
    result = full_stop - delta
    result = max(math.floor(result), full_backward)
    log.debug(f"dynamic_range: {dynamic_range}, range_ratio={range_ratio}, result={result}")
    return result


def apply_control_signal(value):
    global motion_time
    global prev_value
    global motion_duty_cycle

    log.debug(f"new signal value={value}")
    log.debug(f"previous signal value={prev_value}")

    if value > 0.5:
        log.debug("motion forward requested")
        # forward motion
        with motion_duty_cycle_lock:
            motion_duty_cycle = dynamic_range_forward(value)
        if prev_value > 0.5:
            # keep motion
            start_motion_thread()
        if prev_value <= 0.5:
            stop_motion_thread()
            start_motion_thread()

    if value == 0.5:
        log.debug("full stop requested")
        # full stop
        with motion_duty_cycle_lock:
            motion_duty_cycle = full_stop
        if prev_value < 0.5:
            stop_motion_thread()
            go_forward(0.1)
            start_motion_thread()
        if prev_value > 0.5:
            stop_motion_thread()
            start_motion_thread()
        if prev_value == 0.5:
            log.debug("no change required")

    if value < 0.5:
        # backward motion
        log.debug("motion backward requested")
        with motion_duty_cycle_lock:
            motion_duty_cycle = dynamic_range_backward(value)
        if prev_value < 0.5:
            start_motion_thread()
            log.debug("keep backward motion, no change required")
        if prev_value == 0.5 or prev_value > 0.5:
            stop_motion_thread()
            # do not remove, this is start sequence for backward motion
            # required for actual motion
            go_stop(0.1)
            go_backward(0.1)
            go_stop(0.1)
            start_motion_thread()

    prev_value = value
    log.debug(f"new motion_duty_cycle={motion_duty_cycle}")
    log.debug(f"new motion time={motion_time}")


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

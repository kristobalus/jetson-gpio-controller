#!/usr/bin/env python

import Jetson.GPIO as GPIO
import time

full_forward = 55
full_backward = 40
full_stop = 53
pin = 32
frequency = 400
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pin, frequency)
pwm.start(full_stop)


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

try:
    # successful motion backward
    go_forward(10)

    # successful motion backward
    go_stop(0.1)
    go_backward(0.1)
    go_stop(0.1)
    go_backward(10)
    go_forward(0.1)
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    pwm.stop()
    GPIO.cleanup()

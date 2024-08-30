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


def forward():
    for duty_cycle in range(full_stop, full_forward + 1, 1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


def forward_to_stop():
    for duty_cycle in range(full_forward, full_stop - 1, -1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


def backward():
    for duty_cycle in range(full_stop, full_backward - 1, -1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


def backward_to_stop():
    for duty_cycle in range(full_backward, full_stop + 1, 1):
        print(duty_cycle)
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)


try:
    while True:
        forward()
        forward_to_stop()
        time.sleep(3)
        backward()
        backward_to_stop()

finally:
    pwm.stop()
    GPIO.cleanup()

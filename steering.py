#!/usr/bin/env python

import Jetson.GPIO as GPIO
import time
#
# pin 15
# 60 - zero
# 53 - max right
# 66 - max left

neutral_position = 60
max_right = 70
max_left = 50

pin = 15
frequency = 400
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pin, frequency)
pwm.start(neutral_position)


def neutral_left():
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


try:
    while True:
        neutral_left()
        left_to_neutral()
        time.sleep(3)
        neutral_to_right()
        right_to_neutral()

finally:
    pwm.stop()
    GPIO.cleanup()

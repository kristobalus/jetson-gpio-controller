#!/usr/bin/env python

import Jetson.GPIO as GPIO
import time
#
# pin 15
# 60 - zero
# 53 - max right
# 66 - max left

neutral_position = 60
max_right = 53
max_left = 66

pin = 15
frequency = 400
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pin, frequency)
pwm.start(neutral_position)

try:
    while True:
        for duty_cycle in range(0, max_left, 5):
            print(duty_cycle)
            pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.1)
        for duty_cycle in range(max_left, -1, -5):
            print(duty_cycle)
            pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.1)

finally:
    pwm.stop()
    GPIO.cleanup()

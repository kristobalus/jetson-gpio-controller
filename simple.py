#!/usr/bin/env python

import Jetson.GPIO as GPIO
import time

pin = 15
frequency = 400
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pin, GPIO.OUT)

pwm = GPIO.PWM(pin, frequency)
pwm.start(0)

try:
    while True:
        for duty_cycle in range(0, 51, 5):
            print(duty_cycle)
            pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.1)
        for duty_cycle in range(50, -1, -5):
            print(duty_cycle)
            pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.1)

finally:
    pwm.stop()
    GPIO.cleanup()

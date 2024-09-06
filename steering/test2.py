#!/usr/bin/env python

neutral_position = 60
max_right = 70
max_left = 50

pin = 15
frequency = 400
max_left_position = 50

value = float("0.4")
delta = value - 0.5
dynamic_range = abs(neutral_position - max_left_position)
duty_cycle = neutral_position - abs(delta) / 0.5 * dynamic_range
print(f"neutral_position: {neutral_position}")
print(f"max_left_position: {max_left_position}")
print(f"going left, dynamic_range: {dynamic_range}, duty_cycle: {duty_cycle}")


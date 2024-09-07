
import math

full_forward = 63
full_stop = 53
full_backward = 43


def dynamic_range_forward(value):
    if value == 0.5:
        return full_stop
    range_ratio = abs(value - 0.5)/0.5
    dynamic_range = abs(full_forward - full_stop)
    delta = range_ratio * dynamic_range
    result = full_stop + delta
    result = min(math.ceil(result), full_forward)
    print(f"dynamic_range: {dynamic_range}, delta={delta}, range_ratio={range_ratio}, result={result}")
    return result


def dynamic_range_backward(value):
    if value == 0.5:
        return full_stop
    range_ratio = abs(value - 0.5)/0.5
    dynamic_range = abs(full_backward - full_stop)
    delta = range_ratio * dynamic_range
    result = full_stop - delta
    result = max(math.floor(result), full_backward)
    print(f"dynamic_range: {dynamic_range}, range_ratio={range_ratio}, result={result}")
    return result


dynamic_range_forward(1)
dynamic_range_forward(0.8)
dynamic_range_forward(0.7)
dynamic_range_forward(0.6)
dynamic_range_forward(0.5)

print("backward...")
dynamic_range_backward(0.5)
dynamic_range_backward(0.4)
dynamic_range_backward(0.3)
dynamic_range_backward(0.2)
dynamic_range_backward(0.1)
dynamic_range_backward(0)

from homework1.src.task4 import calculate_discount

def test_int_float():
    assert calculate_discount(10, 0.5) == 5.0

def test_float_int():
    assert calculate_discount(3.6, 25) == 2.7

def test_int_int():
    assert calculate_discount(10, 10) == 9

def test_float_float():
    assert calculate_discount(2.5, 0.2) == 2.0
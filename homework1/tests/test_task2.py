from homework1.src.task2 import produce_bool, produce_float, produce_int, produce_string

def test_produce_int():
    assert type(produce_int()) == int

def test_produce_int():
    assert type(produce_float()) == float

def test_produce_int():
    assert type(produce_string()) == str

def test_produce_int():
    assert type(produce_bool()) == bool
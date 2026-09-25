from homework1.src.task3 import pos_neg_zero, print_ten_primes, sum_to_hundred

def test_positive():
    assert pos_neg_zero(1) == "Positive"

def test_negative():
    assert pos_neg_zero(-1) == "Negative"

def test_zero():
    assert pos_neg_zero(0) == "Zero"

def test_ten_primes(capsys):
    print_ten_primes()

    captured = capsys.readouterr()
    assert captured.out == "[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]\n"

def test_sum_to_hundred():
    assert sum_to_hundred() == 5050
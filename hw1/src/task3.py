def pos_neg_zero(num):
    if num == 0:
        return "Zero"
    else:
        return "Positive" if num > 0 else "Negative"

def _is_prime(n):
    if n <= 1:
        return False

    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False

    return True

def print_ten_primes():
    primes = []

    for i in range(10):
        for j in range(50): # hardcoded since we only want first 10 and we know first 10 are all < 50
            if _is_prime(j) and j not in primes:
                primes.append(j)
                break

    print(primes)

def sum_to_hundred():
    i = 0
    sum = 0

    while i <= 100:
        sum += i
        i += 1

    return sum
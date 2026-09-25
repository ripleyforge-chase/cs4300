def calculate_discount(price, discount):
    if discount >= 1:
        discount /= 100

    end_price = price - (price * discount)

    return end_price
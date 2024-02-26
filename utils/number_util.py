import decimal
import random

from utils.constant import tax_rate


def generate_random_number():
    random_number = ''.join([str(random.randint(0, 9)) for _ in range(20)])
    return random_number


def calculate_price_taxed(original_price):
    return (original_price * (1 + decimal.Decimal(tax_rate))).quantize(decimal.Decimal('0.01'))

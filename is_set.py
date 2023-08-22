import timeit
import random


def is_set_bitwise(a, b, c):
    return ((a ^ b) & c) | (a & b & ~c) == 0


def is_set_modulo(a, b, c, d, e, f, g, h, i):
    return (a + b + c) % 3 == 0 and (d + e + f) % 3 == 0 and (g + h + i) % 3 == 0


result = 0
for i in range(100):
    a = random.randrange(0b111111111111)
    b = random.randrange(0b111111111111)
    c = random.randrange(0b111111111111)
    result = result + timeit.timeit(
            lambda: is_set_bitwise(a, b, c),
            number=10000)
print(result / 100)

result = 0
for i in range(100):
    a = random.randrange(0, 3)
    b = random.randrange(0, 3)
    c = random.randrange(0, 3)
    d = random.randrange(0, 3)
    e = random.randrange(0, 3)
    f = random.randrange(0, 3)
    g = random.randrange(0, 3)
    h = random.randrange(0, 3)
    i = random.randrange(0, 3)
    result = result + timeit.timeit(
            lambda: is_set_modulo(a, b, c, d, e, f, g, h, i),
            number=10000)
print(result / 100)

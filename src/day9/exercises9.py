## Day 9 — `Counter` and `defaultdict` 🧠
from collections import Counter
# `Counter(iterable)` counts items. `.most_common(n)` returns the top n as `(item, count)` tuples.
# `defaultdict(factory)`: when you access a missing key, it calls `factory()` to create a default value (e.g. `int` → `0`, `list` → `[]`).
# Docs: https://docs.python.org/3/library/collections.html

# 1. Rewrite `count_occurences` from Day 5 as a one-liner with `Counter`. Print the 2 most common numbers.
numbers = [4, 7, 2, 7, 9, 2, 4, 7]


# Old version from Day 5:
def count_occurences(numbers):
    occurences = {}
    for number in numbers:
        if number in occurences:
            occurences[number] = occurences[number] + 1
        else:
            occurences[number] = 1
    return occurences


print(count_occurences(numbers))

# New version using Counter:
c = Counter(numbers)
print(c.most_common(2))

# 2. Rewrite `calculate_customer_totals` using `defaultdict(float)`. No `if/else` allowed.
orders = [
    {"order_id": 1, "customer": "Anna", "value": 120},
    {"order_id": 2, "customer": "Tom", "value": 80},
    {"order_id": 3, "customer": "Anna", "value": 200},
    {"order_id": 4, "customer": "Kate", "value": 50},
    {"order_id": 5, "customer": "Tom", "value": 150},
]


# Old version from Day 8:
def calculate_customer_totals(orders):
    customer_totals = {}

    for order in orders:
        customer = order["customer"]
        value = order["value"]

        if customer in customer_totals:
            customer_totals[customer] += value
        else:
            customer_totals[customer] = value

    return customer_totals


# New version with defaultdict:
from collections import defaultdict


def calculate_customer_totals(orders):
    customer_totals = defaultdict(float)

    for order in orders:
        customer = order["customer"]
        value = order["value"]

        customer_totals[customer] += value

    return dict(customer_totals)


print(calculate_customer_totals(orders))

# 3. Using the Day 7 `orders` list, build `{customer: [order_id, ...]}` with `defaultdict(list)`.
orders = [
    {"order_id": 1, "customer": "Anna", "value": 120},
    {"order_id": 2, "customer": "Tom", "value": 80},
    {"order_id": 3, "customer": "Anna", "value": 50},
    {"order_id": 4, "customer": "Tom", "value": 40},
    {"order_id": 5, "customer": "Kate", "value": 200},
]


def group_order_ids(orders):
    order_ids_by_customer = defaultdict(list)
    for order in orders:
        order_ids_by_customer[order["customer"]].append(order["order_id"])

    return dict(order_ids_by_customer)


print(group_order_ids(orders))

# 4. Given the review texts below, find the top 3 words. Ignore case and the punctuation `.,!`
reviews = [
    "Great drill, great price!",
    "Drill broke after a week. Bad.",
    "Great service, fast delivery, great drill.",
]

import re


def to_words(text):
    """Turn a sentence into a list of clean, lowercase words."""
    return re.findall(r"[\w']+", text.lower())


all_words = []
for review in reviews:
    all_words.extend(to_words(review))

print(Counter(all_words).most_common(3))


# **Stretch:** use `Counter` arithmetic. Given `stock_before` and `items_sold` as Counters, compute `stock_after = stock_before - items_sold`. What happens to items that drop to zero?

# **Check yourself**
# 1. What happens when you read a missing key from `defaultdict(list)`?
# “It calls list(), inserts an empty list under that key, and returns it, so .append() works straight away.”
# 2. What's the difference between `d.get("x", 0)` on a normal dict and `dd["x"]` on a `defaultdict(int)`? Why can that difference cause a bug?
# “.get('x', 0) returns 0 but doesn’t change the dict. dd['x'] inserts 'x': 0. So if you only meant to check a key, you’ve created a phantom entry, and a customer with no orders suddenly shows up in the report with 0.”
# 3. What does `Counter("banana").most_common(1)` return?
# A Counter loops over whatever you give it, and looping over a string gives you characters, not the whole word:
# 4. Why does `defaultdict(0)` fail?
# “The argument must be a callable that produces the default, like int, list or lambda: 0. 0 is a value, not something Python can call.”

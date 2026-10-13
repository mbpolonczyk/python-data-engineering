# Exercise 1 — Debug the function
# The function is supposed to calculate the total value of all orders, but it produces the wrong result.
orders = [
    {"customer": "Anna", "value": 120},
    {"customer": "Tom", "value": 80},
    {"customer": "Anna", "value": 200},
    {"customer": "Kate", "value": 50},
]


# = (assign/replace) and += (add to the existing value)
def calculate_total(orders):
    total = 0

    for order in orders:
        total += order["value"]

    return total


print(calculate_total(orders))

# Exercise 2 — Handle an empty list
# Modify the function so it handles an empty list without raising an error.


def calculate_average_order_value(orders):
    if not orders:
        return 0

    total = 0
    for order in orders:
        total += order["value"]

    return total / len(orders)


print(calculate_average_order_value([]))

# Exercise 3 — Handle missing dictionary keys
# Your task is to write calculate_total(orders) that returns 170,
# ignoring orders that don't contain a "value" key.
orders = [
    {"customer": "Anna", "value": 120},
    {"customer": "Tom"},
    {"customer": "Kate", "value": 50},
]


def calculate_total(orders):
    total = 0

    for order in orders:
        value = order.get(
            "value"
        )  # returns the value if the key exists, or None if it doesn't
        if value is not None:
            total += value

    return total


print(calculate_total(orders))

# order["value"]       # Raises KeyError if missing
# order.get("value")   # Returns None if missing

# Exercise 4 — Combine filtering and aggregation
# Write a function calculate_large_order_total(orders, minimum_value)
# that returns the total value of orders strictly greater than minimum_value.
orders = [
    {"customer": "Anna", "value": 120},
    {"customer": "Tom", "value": 80},
    {"customer": "Anna", "value": 200},
    {"customer": "Kate", "value": 50},
    {"customer": "Tom", "value": 150},
]


def calculate_large_order_total(orders, minimum_value):
    total = 0
    for order in orders:
        value = order.get("value")

        if value is not None and value > minimum_value:
            total += value

    return total


print(calculate_large_order_total(orders, 100))

# Exercise 5 — Your mini interview challenge
# Write a function calculate_customer_totals(orders) that:
# Groups orders by customer.
# Sums each customer's valid numeric order values.
# Ignores missing "value" keys.
# Ignores values that cannot be converted to numbers, such as "invalid".
orders = [
    {"customer": "Anna", "value": 120},
    {"customer": "Tom", "value": 80},
    {"customer": "Anna", "value": 200},
    {"customer": "Kate"},
    {"customer": "Tom", "value": 150},
    {"customer": "Anna", "value": "invalid"},
]


def calculate_customer_totals(orders):
    customer_totals = {}
    for order in orders:
        customer = order["customer"]
        value = order.get("value")

        if value is None:
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if customer in customer_totals:
            customer_totals[customer] += value
        else:
            customer_totals[customer] = value

    return customer_totals


print(calculate_customer_totals(orders))

# Exercise 6
orders = [
    {"customer": "Anna", "value": 80},
    {"customer": "Tom", "value": 150},
    {"customer": "Kate", "value": 200}
]

def find_first_large_order(orders, minimum_value):
    for order in orders:
        if order["value"] > minimum_value:
            customer = order["customer"]

            return customer
    return None # The function checks every order and returns None only if no match is found

print(find_first_large_order(orders, 100))
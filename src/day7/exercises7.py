# Exercise 1 — Calculate customer totals
# Write a function called calculate_customer_totals(orders)
# that returns a dictionary containing the total order value for each customer.

orders = [
    {"order_id": 1, "customer": "Anna", "value": 120},
    {"order_id": 2, "customer": "Tom", "value": 80},
    {"order_id": 3, "customer": "Anna", "value": 50},
    {"order_id": 4, "customer": "Tom", "value": 40},
    {"order_id": 5, "customer": "Kate", "value": 200},
]


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


print(calculate_customer_totals(orders))

# Exercise 2 — Find the first large order
# The function should return the first order dictionary whose value is greater than minimum_value.


def find_first_large_order(orders, minimum_value):
    for order in orders:
        if order["value"] > minimum_value:
            return order
    return None


print(find_first_large_order(orders, 100))

# Exercise 3 — Handle missing values
# Write a function called calculate_valid_order_total(orders) that returns the sum of all valid order values.

orders = [
    {"order_id": 1, "customer": "Anna", "value": 120},
    {"order_id": 2, "customer": "Tom", "value": None},
    {"order_id": 3, "customer": "Anna", "value": 50},
    {"order_id": 4, "customer": "Kate"},
    {"order_id": 5, "customer": "Tom", "value": 40},
]


def calculate_valid_order_total(orders):
    total = 0

    for order in orders:
        value = order.get("value")

        if value is None:
            continue

        total += value
    return total


print(calculate_valid_order_total(orders))

# Exercise 4 — Find the top customer
# The function should return the name of the customer with the highest total order value,
# not the customer with the single largest order.

orders = [
    {"order_id": 1, "customer": "Anna", "value": 120},
    {"order_id": 2, "customer": "Tom", "value": 80},
    {"order_id": 3, "customer": "Anna", "value": 50},
    {"order_id": 4, "customer": "Tom", "value": 40},
    {"order_id": 5, "customer": "Kate", "value": 200},
]


def find_top_customer(orders):
    customer_totals = calculate_customer_totals(orders)

    if not customer_totals:
        return None
    else:
        highest_total = max(customer_totals.values())

    for customer, value in customer_totals.items():
        if value == highest_total:
            return customer


print(find_top_customer(orders))

# Exercise 5 — Calculate the average order value


def calculate_average_order_value(orders):
    totals = 0
    count = 0

    if not orders:
        return None

    for order in orders:
        if order.get("value") is not None:
            totals += order["value"]
            count += 1

    if count == 0:
        return 0

    return totals / count


print(calculate_average_order_value(orders))

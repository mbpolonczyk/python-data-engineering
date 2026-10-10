# Exercise 1 - Validate order values
def parse_order_value(value):
    try:
        number = float(value)
        return number
    except ValueError:
        return None


print(parse_order_value("125.50"))
print(parse_order_value("80"))
print(parse_order_value("abc"))

# Exercise 2 - Process a list of orders
order_values = ["120.50", "80", "abc", "45.5", "invalid", "200"]


def process_order_values(order_values):
    valid_orders = []  # empty list
    for value in order_values:
        number = parse_order_value(value)
        if number is not None:
            valid_orders.append(number)
    return valid_orders


print(process_order_values(order_values))

# Exercise 3 - Calculate the total
order_values = ["120.50", "80", "abc", "45.5", "invalid", "200"]


def calculate_valid_total(order_values):
    valid_orders = process_order_values(order_values)

    if not valid_orders:
        return 0

    return sum(valid_orders)


print(calculate_valid_total(order_values))

# Exercise 4 - Final challenge: A mini mock assessment
# Loops through the orders.
# Selects only orders belonging to the specified customer.
# Converts each selected order's value using parse_order_value().
# Skips invalid values.
# Returns the total for that customer, or 0 if there are no valid orders.

orders = [
    {"customer": "Anna", "value": "120.50"},
    {"customer": "Tom", "value": "abc"},
    {"customer": "Anna", "value": "80"},
    {"customer": "Kate", "value": "45.5"},
    {"customer": "Tom", "value": "200"},
]


def get_customer_total(orders, customer):
    order_value = 0

    for order in orders:
        if order["customer"] == customer:
            value = order["value"]
            valid_value = parse_order_value(value)

            if valid_value is not None:
                order_value += valid_value

    return order_value


print(get_customer_total(orders, "Tom"))
print(get_customer_total(orders, "Anna"))

# Exercise 1 — List comprehensions
# Write code to solve these three problems:
# 1. Create a list containing the values of all orders.
# 2. Create a list containing only orders with a value greater than 100.
# 3. Create a list containing the names of customers whose orders are greater than 100.
orders = [
    {"order_id": 1, "customer": "Anna", "value": 120},
    {"order_id": 2, "customer": "Tom", "value": 80},
    {"order_id": 3, "customer": "Anna", "value": 200},
    {"order_id": 4, "customer": "Kate", "value": 50},
    {"order_id": 5, "customer": "Tom", "value": 150},
]

orders_values = [order["value"] for order in orders]
print(orders_values)

large_orders = [order for order in orders if order["value"] > 100]
print(large_orders)

large_order_customers = [order["customer"] for order in orders if order["value"] > 100]
print(large_order_customers)

# Exercise 2 — Sorting with sorted() and lambda
# Using the same orders list, write code to:
# 1. Sort orders by value from lowest to highest.
# 2. Sort orders by value from highest to lowest.
# 3. Extract the customer totals using your existing calculate_customer_totals() function from previous exercises, then sort those totals from highest to lowest.

sorted_orders = sorted(orders, key=lambda order: order["value"])
print(sorted_orders)

sorted_orders = sorted(orders, key=lambda order: order["value"], reverse=True)
print(sorted_orders)


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


customer_totals = calculate_customer_totals(orders)
sorted_by_customer = sorted(
    customer_totals.items(), key=lambda item: item[1], reverse=True
)
print(sorted_by_customer)
# customer_totals.items() returns key-value pairs, such as ("Anna", 320).
# item[0] is the customer name
# item[1] is the customer's total

# Exercise 3 - Combine filtering, aggregation and sorting
# Let's put these concepts together in a small interview-style challenge.
# Using the same orders list, write a function called get_top_customers(orders, minimum_total) that:
# 1. Calculates the total value for each customer.
# 2. Keeps only customers whose total is greater than or equal to minimum_total.
# 3. Sorts the remaining customers by total, highest first.
# 4. Returns a list of tuples: (customer, total).


def get_top_customers(orders, minimum_total):
    customer_totals = calculate_customer_totals(orders)

    large_orders = []
    for customer, value in customer_totals.items():
        if value >= minimum_total:
            large_orders.append((customer, value))

    sorted_large_orders = sorted(
        large_orders, key=lambda order: order[1], reverse=True
    )  # order[1] → customer total

    return sorted_large_orders


print(get_top_customers(orders, 100))


def get_top_customers(orders, minimum_total):
    customer_totals = calculate_customer_totals(orders)

    large_orders = [
        (customer, value)
        for customer, value in customer_totals.items()
        if value >= minimum_total
    ]

    sorted_large_orders = sorted(
        large_orders, key=lambda order: order[1], reverse=True
    )  # order[1] → customer total

    return sorted_large_orders


print(get_top_customers(orders, 100))

# Final challenge
# Write a function called get_large_order_summary(orders, minimum_value) that returns a dictionary containing:
# - large_orders: a list of orders with a value strictly greater than minimum_value
# - large_order_count: the number of qualifying orders
# - large_order_total: the sum of their values
# - average_large_order: their average value, or 0 if no orders qualify


def get_large_order_summary(orders, minimum_value):

    large_orders = [order for order in orders if order["value"] > minimum_value]
    large_order_count = len(large_orders)
    large_order_total = sum(order["value"] for order in large_orders)

    summary = {
        "large_orders": large_orders,
        "large_order_count": large_order_count,
        "large_order_total": large_order_total,
        "average_large_order": (
            round(large_order_total / large_order_count, 2)
            if large_order_count > 0
            else 0
        ),
    }

    return summary


print(get_large_order_summary(orders, 100))

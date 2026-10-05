orders = [
    {"order_id": 1, "customer": "Anna", "value": 120.50},
    {"order_id": 2, "customer": "John", "value": 89.99},
    {"order_id": 3, "customer": "Anna", "value": 240.00},
    {"order_id": 4, "customer": "Kate", "value": 55.50},
    {"order_id": 5, "customer": "John", "value": 310.00},
]


# Create function for orders per customer
def calculate_total_by_customer(orders, customer):
    total = 0
    for order in orders:
        if order["customer"] == customer:
            total += order["value"]
    return total


outcome = calculate_total_by_customer(orders, "Anna")
print(f"outcome is: {outcome}")


# Create function for customer summary
def customer_summary(orders, customer):
    total = 0
    count = 0

    for order in orders:
        if order["customer"] == customer:
            total += order["value"]
            count += 1
    return {"total": total, "count": count}


summary = customer_summary(orders, "Anna")
print(f"Total: {summary['total']}, Number of orders: {summary['count']}")


def customer_summary2(orders, customer):
    total = 0
    count = 0

    for order in orders:
        if order["customer"] == customer:
            total += order["value"]
            count += 1
    return total, count  # this creates a tuple


summary_total, summary_count = customer_summary2(orders, "Anna")
print(f"Total: {summary_total}, Number of orders: {summary_count}")

# Create a list comprehension for John's orders
# List comprehension offers a shorter syntax when you want to create a new list based on the values of an existing list.
john_orders = [order for order in orders if order["customer"] == "John"]
print(john_orders)

# Create a list comprehension for John's orders values
john_orders_values = [order["value"] for order in orders if order["customer"] == "John"]
print(john_orders_values)

# Create a total of John's orders using SUM
# Generator expression
john_total = sum(order["value"] for order in orders if order["customer"] == "John")

print(john_total)

# Sorting
sorted_orders = sorted(orders, key=lambda order: order["value"], reverse=True)

print(sorted_orders)

# Sorting large orders
large_orders = sorted(
    [order for order in orders if order["value"] > 100],
    key=lambda order: order["value"],
    reverse=True,
)
print(large_orders)

# List of customer names whose order is worth more than 100, sorted by order value from highest to lowest
customers_with_large_orders = [order["customer"] for order in large_orders]
print(customers_with_large_orders)

# Group by
customer_totals = {}  # creating a dict

for order in orders:
    customer = order["customer"]
    value = order["value"]
    if customer not in customer_totals:
        customer_totals[customer] = 0
    customer_totals[customer] += value
print(customer_totals)

# Group by + Count
customer_summary = {}  # creating a dict

for order in orders:
    customer = order["customer"]
    value = order["value"]

    if customer not in customer_summary:
        customer_summary[customer] = {"total": 0, "count": 0}
    customer_summary[customer]["total"] += value
    customer_summary[customer]["count"] += 1
print(customer_summary)

# Average order value, dictionary iteration and transformation
average_order_value = {}  # creating a dict
for (
    customer,
    data,
) in customer_summary.items():  # .items() gives you each key and value together
    average_order_value[customer] = data["total"] / data["count"]
print(average_order_value)

# Customer report with all the information
customer_report = {}
for customer, data in customer_summary.items():
    customer_report[customer] = {
        "total": data["total"],
        "count": data["count"],
        "average": data["total"] / data["count"],
    }
print(customer_report)

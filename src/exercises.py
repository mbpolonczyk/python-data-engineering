orders = [
    {"order_id": 1, "customer": "Anna", "value": 120.50},
    {"order_id": 2, "customer": "John", "value": 89.99},
    {"order_id": 3, "customer": "Anna", "value": 240.00},
    {"order_id": 4, "customer": "Kate", "value": 55.50},
    {"order_id": 5, "customer": "John", "value": 310.00},
]
# Total revenue 
total = 0
for order in orders:
    total = total + order["value"]

total = sum(order["value"] for order in orders)

print(f"Total value of orders is: {total}.")

# Number of orders
orders_count = len(orders)
print(f"Number of orders: {orders_count}.")

# Average order value
avg_order = total / orders_count
print(f"Average order value: {avg_order}.")

# Calculate how much each customer spent in total
totals = {}

for order in orders:
    customer = order["customer"]
    value = order["value"]

    if customer in totals:
        totals[customer] = totals[customer] + value
    else:
        totals[customer] = value

for customer, total in totals.items():
    print(f"{customer} spent {total:.2f}")

# Customer with the highest total spend
top_customer = None
top_total = 0

for customer, total in totals.items():
    if total > top_total:
        top_customer = customer
        top_total = total

print(f"Top customer is {top_customer} with {top_total:.2f}")

# Total revenue only for orders greater than 100
gt100_orders = sum(order["value"] for order in orders if order["value"] > 100)
print(f"Total revenue only for orders greater than 100 is: {gt100_orders}.")

# Create function for that
def calculate_total(orders):
    return sum(order["value"] for order in orders)

total = calculate_total(orders)
print(total)




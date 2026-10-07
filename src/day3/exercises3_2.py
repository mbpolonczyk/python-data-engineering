# 3.2 Working with JSON

# Exercise1: Read the orders.json
import json

with open("src/day3/orders.json", "r") as file:
    orders = json.load(file)
for order in orders:
    order_id = order["order_id"]
    customer = order["customer"]
    print(order_id, customer)

# Exercise2: Calculate from JSON
total = 0
order_count = 0
for order in orders:
    value = order["value"]
    total += value
    order_count += 1
print(f"Total order value: {total} \nNumber of orders: {order_count}")

# Exercise3: Customer total
customer_totals = {}

for order in orders:
    customer = order["customer"]
    value = order["value"]

    customer_totals[customer] = customer_totals.get(customer, 0) + value
    # dict.get() means: "Give me the value for this key, or give me 0 if the key doesn't exist."

for customer, total in customer_totals.items():
    print(f"{customer} -> {total:.2f}")

# Exercise4: json.dump()
total = 0
order_count = 0

for order in orders:
    total += order["value"]
    order_count += 1

summary = {"total": total, "order_count": order_count}

with open("src/day3/summary.json", "w") as file:
    json.dump(summary, file, indent=4)

# Exercise5: Read back the JSON created
with open("src/day3/summary.json", "r") as file:
    summary = json.load(file)
summary_total = summary["total"]
summary_count = summary["order_count"]
print(f"Total: {summary_total} \nOrders: {summary_count}")

# Exercise6: Basic error handling
try:
    with open("src/day3/broken.json", "r") as file:
        orders = json.load(file)
except FileNotFoundError:
    print("File not found.")
except json.JSONDecodeError:
    print("Invalid JSON.")
else:
    print("File loaded successfully.")
finally:  # runs regardless of whether an error occurred.
    print("Finished.")


# Exercise7: Create load_orders function
def load_orders(filename):
    try:
        with open(filename, "r") as file:
            orders = json.load(file)
    except FileNotFoundError:
        print("File not found.")
        return None
    except json.JSONDecodeError:
        print("Invalid JSON.")
        return None
    else:
        return orders


print(load_orders("src/day3/orders.json"))


# Final project
def process_orders(input_file, output_file):
    orders = load_orders(input_file)

    if orders is None:
        return None

    total = 0
    order_count = 0
    customer_totals = {}

    for order in orders:
        value = order["value"]
        customer = order["customer"]

        total += value
        order_count += 1

        customer_totals[customer] = customer_totals.get(customer, 0) + value

    print(total, order_count)
    print(customer_totals)

    summary = {
        "total": total,
        "order_count": order_count,
        "customer_totals": customer_totals,
    }

    with open(output_file, "w") as file:
        json.dump(summary, file, indent=4)

    return summary


summary = process_orders("src/day3/orders.json", "src/day3/summary.json")

print(summary)

orders = [
    {"customer": "Anna", "product": "Laptop", "value": 1200},
    {"customer": "John", "product": "Mouse", "value": 50},
    {"customer": "Anna", "product": "Keyboard", "value": 150},
    {"customer": "John", "product": "Laptop", "value": 1000},
    {"customer": "Kate", "product": "Monitor", "value": 400},
    {"customer": "Anna", "product": "Mouse", "value": 50},
    {"customer": "John", "product": "Keyboard", "value": 120},
]

# # Your manager wants a report containing one entry per customer like
# {
#     "Anna": {
#         "total": 1400,
#         "orders": 3,
#         "average": 466.67
#     }
# }

customer_totals = {}

for order in orders:
    customer = order["customer"]
    value = order["value"]
    if customer not in customer_totals:
        customer_totals[customer] = {"total": 0, "count": 0}
    customer_totals[customer]["total"] += value
    customer_totals[customer]["count"] += 1
print(customer_totals)

customer_report = {}

for customer, data in customer_totals.items():
    customer_report[customer] = {
        "total": data["total"],
        "count": data["count"],
        "average": data["total"] / data["count"],
    }
print(customer_report)

# Sort the output from the highest total to lowest
customer_report_sorted = sorted(
    customer_report.items(),
    key=lambda item: item[1]["total"],
    reverse=True,
)
print(customer_report_sorted)

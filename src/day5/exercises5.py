# Exercise 1 — Count occurrences
# Write a function called count_occurrences(numbers) that returns a dictionary showing how many times each number appears.
# Expected result: {4: 2, 7: 3, 2: 2, 9: 1}

numbers = [4, 7, 2, 7, 9, 2, 4, 7]

# Solution:
# I create an empty dictionary and iterate through the list.
# If a number is already a key, I increment its count;
# otherwise, I initialize it to one.
# Finally, I return the dictionary.


def count_occurences(numbers):
    occurences = {}
    for number in numbers:
        if number in occurences:
            occurences[number] = occurences[number] + 1
        else:
            occurences[number] = 1
    return occurences


print(count_occurences(numbers))

# Exercise 2 — Find duplicates
# Write a function called find_duplicates(numbers) that returns a list of numbers that appear more than once,
# without repeating any number in the result.

numbers = [4, 7, 2, 7, 9, 2, 4, 7]


def find_duplicates(numbers):
    duplicates = []
    occurences = count_occurences(numbers)

    for number, count in occurences.items():
        # print(number, count)

        if count > 1:
            duplicates.append(number)

    return duplicates


print(find_duplicates(numbers))

# Exercise 3 — Filter and transform data
# Write a function get_large_orders(orders, minimum_value) that returns a list
# containing only orders whose value is greater than minimum_value.
orders = [
    {"customer": "Anna", "value": 120},
    {"customer": "Tom", "value": 80},
    {"customer": "Anna", "value": 200},
    {"customer": "Kate", "value": 50},
    {"customer": "Tom", "value": 150},
]


def get_large_orders(orders, minimum_value):
    large_orders = []
    for order in orders:
        value = order["value"]
        if value > minimum_value:
            large_orders.append(order)
    return large_orders


print(get_large_orders(orders, 100))

# Exercise 4 — Count matching items
# Using the same orders list, write a function count_large_orders(orders, minimum_value).
# It should return the number of orders whose value is greater than minimum_value.
# Example: count_large_orders(orders, 100) should return 3.


def count_large_orders(orders, minimum_value):
    large_orders = get_large_orders(orders, minimum_value)
    return len(large_orders)  # instead of looping through orders and adding count


print(count_large_orders(orders, 100))

# Exercise 5 — Aggregate data by customer
# Using the same orders list, write a function calculate_customer_totals(orders) that
# returns a dictionary containing each customer's total order value.
# Expected result:
# {
#     "Anna": 320,
#     "Tom": 230,
#     "Kate": 50
# }


def calculate_customer_totals(orders):
    customer_total = {}
    for order in orders:
        customer = order["customer"]
        value = order["value"]

        if customer in customer_total:
            customer_total[customer] += value
        else:
            customer_total[customer] = value
    return customer_total


print(calculate_customer_totals(orders))

# Exercise 6 — Find the customer with the highest total
# Write find_top_customer(orders) that returns the name of the customer with the highest total order value.


def find_top_customer(orders):
    customer_totals = calculate_customer_totals(orders)

    if not customer_totals:
        return None # max() on an empty collection raises a ValueError
    else:
        highest_total = max(
            customer_totals.values()
        )  # max() can find the largest value in a list

    for customer, value in customer_totals.items():
        if value == highest_total:
            return customer


print(find_top_customer(orders))

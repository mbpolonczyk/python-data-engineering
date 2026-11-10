# Day 10 — Big-O and choosing data structures
# Goal: pick list / set / dict based on how you look things up, and say the complexity.
# Imports go here, at the top (yesterday's review point).
import timeit


# 1. Compare `999_999 in big_list` with `999_999 in big_set` (1,000,000 ints each).
#    Before you run it: guess how many times faster the set will be.
big_list = list(range(1_000_000))
big_set = set(big_list)

# guess: ~1,000,000x because a list needs to scan every item, set needs to do 1 check

# your timeit code here
big_list_time = timeit.timeit(lambda: 999_999 in big_list, number=100)
big_set_time = timeit.timeit(lambda: 999_999 in big_set, number=100)
print(big_list_time / big_set_time)

# measured: ~105,000x

# 2. Rewrite `find_duplicates` in ONE pass, with two sets: `seen` and `duplicates`.
#    Old version (Day 5) — note it needs count_occurences first, then a second loop:
#
#    def find_duplicates(numbers):
#        duplicates = []
#        occurences = count_occurences(numbers)
#        for number, count in occurences.items():
#            if count > 1:
#                duplicates.append(number)
#        return duplicates
numbers = [4, 7, 2, 7, 9, 2, 4, 7]


def find_duplicates(numbers):
    seen = set()
    duplicates = set()

    for number in numbers:
        if number in seen:
            duplicates.add(number)
        else:
            seen.add(number)
    return duplicates


print(find_duplicates(numbers))  # expected: {2, 4, 7} (any order)


# 3. Two-sum: return the indices of two orders whose values add up to the budget.
values = [120, 80, 200, 50, 150]
budget = 250


# Version A: nested loops, O(n²)
def two_sum_slow(values, budget):
    for i in range(len(values)):
        for j in range(i+1, len(values)):
            if values[i] + values[j] == budget:
                return (i,j)
    return None

# Version B: one pass with a dict {value: index}, O(n)
def two_sum_fast(values, budget):
    seen = {}
    for i in range(len(values)):
        needed = budget - values[i]
        if needed in seen:
            return (seen[needed], i) 
        seen[values[i]] = i
    return None


print(two_sum_slow(values, budget))  # expected: (2, 3)  -> 200 + 50
print(two_sum_fast(values, budget))  # expected: (2, 3)


# 4. Return the customers who are new today, in the order they appear today.
yesterday_customers = ["Anna", "Tom", "Kate", "Piotr"]
today_customers = ["Ola", "Tom", "Marek", "Anna", "Ola", "Ewa"]


def new_customers(yesterday, today):
    yesterday = set(yesterday)
    seen = set()
    result = []
    for customer in today:
        if customer not in yesterday and customer not in seen:
            result.append(customer)
            seen.add(customer)
    return result

print(
    new_customers(yesterday_customers, today_customers)
)  # expected: ['Ola', 'Marek', 'Ewa']


# ⭐ Stretch: `list(dict.fromkeys(items))` dedupes a list and keeps the order. Why does it work?
# “dict.fromkeys dedupes because dict keys are unique, and it keeps the order because dicts preserve insertion order since Python 3.7. 
# It’s a one-liner for an order-preserving dedupe.”

# items = ["Ola", "Tom", "Ola", "Ewa"]
# dict.fromkeys(items)        # {'Ola': None, 'Tom': None, 'Ewa': None} it makes each item a key with the value None
# list(dict.fromkeys(items))  # ['Ola', 'Tom', 'Ewa']

# Check yourself — answer as comments (write EXACT outputs/complexities):
# 1. What's the complexity of version A and version B in task 3?
# Version A uses two nested loops, so its time complexity is O(n²) and its memory is O(1).
# Version B uses one loop, and each dict lookup is O(1), so its time is O(n).
# The trade-off: B needs O(n) memory for the `seen` dict.

# 2. Why are dict and set lookups fast?
# The key is hashed into a number that works like an address, so Python jumps
# straight to the right slot instead of scanning every item like a list does.
# That makes a lookup O(1) on average.

# 3. Can a list be a dict key? What would you use instead?
# The reason a list can’t be a key is that a list can change (it’s mutable), so its hash “shelf address” could break. That’s what unhashable means.
# A set can’t be a key either, for the same reason: it can change too.
# Use a tuple: {("Anna", 2026): 320}

# 4. You need to dedupe 50 million order IDs and keep their order. How, and what's the trade-off?
# One pass with list(dict.fromkeys(order_ids)), or a `seen` set plus a result list.
# Dict keys are unique and dicts keep insertion order (Python 3.7+).
# Time is O(n), but memory is also O(n): 50M IDs can take several GB of RAM.
# If they don't fit, push the dedupe to the database (ROW_NUMBER()) or Spark (dropDuplicates).
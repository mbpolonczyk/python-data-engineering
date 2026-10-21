## Day 9 — `Counter` and `defaultdict` 🧠
from collections import Counter, defaultdict
# `Counter(iterable)` counts items. `.most_common(n)` returns the top n as `(item, count)` tuples.
# `defaultdict(factory)`: when you access a missing key, it calls `factory()` to create a default value (e.g. `int` → `0`, `list` → `[]`).
# Docs: https://docs.python.org/3/library/collections.html

# **Do (30 min)** in `src/day9/exercises9.py`
# 1. Rewrite `count_occurences` from Day 5 as a one-liner with `Counter`. Print the 2 most common numbers.
numbers = [4, 7, 2, 7, 9, 2, 4, 7]


# Old version from Day 5:
def count_occurences(numbers):
    occurences = {}
    for number in numbers:
        if number in occurences:
            occurences[number] = occurences[number] + 1
        else:
            occurences[number] = 1
    return occurences


print(count_occurences(numbers))

# New version using Counter:
c = Counter(numbers)
print(c.most_common(2))

# 2. Rewrite `calculate_customer_totals` using `defaultdict(float)`. No `if/else` allowed.
# 3. Using the Day 7 `orders` list, build `{customer: [order_id, ...]}` with `defaultdict(list)`.
# 4. Given the review texts below, find the top 3 words. Ignore case and the punctuation `.,!`
#    ```python
#    reviews = [
#        "Great drill, great price!",
#        "Drill broke after a week. Bad.",
#        "Great service, fast delivery, great drill.",
#    ]
#    ```

# **Stretch:** use `Counter` arithmetic. Given `stock_before` and `items_sold` as Counters, compute `stock_after = stock_before - items_sold`. What happens to items that drop to zero?

# **Check yourself**
# 1. What happens when you read a missing key from `defaultdict(list)`?
# 2. What's the difference between `d.get("x", 0)` on a normal dict and `dd["x"]` on a `defaultdict(int)`? Why can that difference cause a bug?
# 3. What does `Counter("banana").most_common(1)` return?
# 4. Why does `defaultdict(0)` fail?

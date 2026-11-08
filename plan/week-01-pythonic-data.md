# Week 1 · Pythonic data handling

**Phase 1 — Python that pipelines are made of** · Days 9–13
[← Plan overview](README.md) · [Week 2 →](week-02-files-packages-tests.md)

> **This week's outcome:** you replace hand-written loops from days 1–8 with the standard tools that experienced engineers use, and you can explain *why* one approach is faster than another.
>
> **Project milestone:** none yet. This week sharpens the tools you'll use in every connector and transformation from Week 2 onwards.

| Day | Topic | Time |
|---|---|---|
| 9 | `Counter` and `defaultdict` | ~40 min |
| 10 | Big-O and choosing data structures | ~45 min |
| 11 | Unpacking, `zip`, `enumerate`, `any`/`all`, mutability | ~45 min |
| 12 | Functions in depth | ~50 min |
| 13 | 🛠 Build day: timed cleaning challenge + quiz | ~50 min |

---

<a id="day-9"></a>
## Day 9 · `Counter` and `defaultdict`

⏱ ~40 min · 📁 `src/day9/exercises9.py`

> 🎯 **By the end you can:** replace "if key in dict… else…" grouping loops with `Counter` and `defaultdict`.
> 💼 **At work:** almost every transformation step groups or counts something.

### 📖 Learn (10 min)
- `from collections import Counter, defaultdict`
- `Counter(iterable)` counts items. `.most_common(n)` returns the top n as `(item, count)` tuples.
- `defaultdict(factory)`: when you access a missing key, it calls `factory()` to create a default value (`int` → `0`, `list` → `[]`).
- Docs: https://docs.python.org/3/library/collections.html

### 💻 Do (25 min)
- [ ] **1.** Rewrite `count_occurences` from Day 5 as a one-liner with `Counter`. Print the 2 most common numbers.
- [ ] **2.** Rewrite `calculate_customer_totals` using `defaultdict(float)`. No `if/else` allowed.
- [ ] **3.** Using the Day 7 `orders` list, build `{customer: [order_id, ...]}` with `defaultdict(list)`.
- [ ] **4.** Find the top 3 words in these reviews. Ignore case and the punctuation `.,!`
  ```python
  reviews = [
      "Great drill, great price!",
      "Drill broke after a week. Bad.",
      "Great service, fast delivery, great drill.",
  ]
  ```
- ⭐ *Stretch:* compute `stock_after = stock_before - items_sold`, where both are Counters. What happens to items that drop to zero?

### ✅ Check yourself (5 min)
1. What happens when you read a missing key from `defaultdict(list)`?
2. What's the difference between `d.get("x", 0)` on a dict and `dd["x"]` on a `defaultdict(int)`? Why can it cause a bug?
3. What does `Counter("banana").most_common(1)` return?
4. Why does `defaultdict(0)` fail?

<details><summary>Answers</summary>

1. It calls `list()`, **inserts** the empty list under that key, and returns it.
2. `.get` doesn't change the dict. Reading `dd["x"]` **creates the key** as a side effect. If you only meant to check it, you've now added an entry with value `0`, which can make "missing" customers show up in your output.
3. `[('a', 3)]`
4. The argument must be a *callable* that produces a default, like `int`, `list` or `lambda: 0`. `0` isn't callable.
</details>

---

<a id="day-10"></a>
## Day 10 · Big-O and choosing data structures

⏱ ~45 min · 📁 `src/day10/exercises10.py`

> 🎯 **By the end you can:** choose between a list, set and dict based on how you'll look things up, and state the complexity.
> 💼 **At work:** the wrong structure turns a 2-second dedupe into a 2-hour one.

### 📖 Learn (15 min)
- Big-O describes how runtime grows with input size `n`: `O(1)`, `O(n)`, `O(n log n)` (sorting), `O(n²)` (nested loops).
- `x in list` is **O(n)** because it scans every element. `x in set` and `key in dict` are **O(1) on average** because of hashing.
- Only hashable (immutable) values can be set members or dict keys: `str`, `int`, `tuple`. Lists and dicts can't.

### 💻 Do (25 min)
- [ ] **1.** Use `timeit` to compare `999_999 in big_list` with `999_999 in big_set` (1,000,000 ints each):
  ```python
  import timeit
  big_list = list(range(1_000_000)); big_set = set(big_list)
  print(timeit.timeit(lambda: 999_999 in big_list, number=100))
  ```
- [ ] **2.** Rewrite `find_duplicates` from Day 5 in **one pass**, with two sets: `seen` and `duplicates`.
- [ ] **3.** *Two-sum:* given `values = [120, 80, 200, 50, 150]` and `budget = 250`, return the indices of two orders that add up to the budget. Write version A with nested loops (`O(n²)`), then version B in one pass with a dict `{value: index}` (`O(n)`).
- [ ] **4.** Given `yesterday_customers` and `today_customers` (both lists), return the customers who are new today, **in the order they appear today**.
- ⭐ *Stretch:* `list(dict.fromkeys(items))` dedupes a list and keeps the order. Why does it work?

### ✅ Check yourself (5 min)
1. What's the complexity of version A and version B in task 3?
2. Why are dict and set lookups fast?
3. Can a list be a dict key? What would you use instead?
4. You need to dedupe 50 million order IDs and keep their order. How would you do it, and what's the trade-off?

<details><summary>Answers</summary>

1. A is `O(n²)`. B is `O(n)`, because each dict lookup is `O(1)`.
2. The key is hashed into a number that points almost directly to where the value is stored. There's no scanning.
3. No. Lists are mutable, so they're unhashable. Use a tuple.
4. Loop once, keeping a `seen` set and appending unseen IDs to the output. That's `O(n)` time but also `O(n)` memory. If it doesn't fit in memory, push the work to a database (`ROW_NUMBER`) or to Spark (Week 9).
</details>

---

<a id="day-11"></a>
## Day 11 · Unpacking, `zip`, `enumerate`, `any`/`all`, mutability

⏱ ~45 min · 📁 `src/day11/exercises11.py`

> 🎯 **By the end you can:** write idiomatic loops, and avoid the classic "I changed a copy and the original changed too" bug.
> 💼 **At work:** mutability bugs silently corrupt data, and nobody notices until a report is wrong.

### 📖 Learn (10 min)
- `for i, order in enumerate(orders, start=1)`
- `zip(a, b)` pairs up elements. `zip(a, b, strict=True)` raises an error if the lengths differ.
- `any(...)` and `all(...)` take generator expressions.
- Comprehensions: `{k: v for ...}` builds a dict, `{x for ...}` builds a set.
- `b = a` doesn't copy anything. Both names point to the **same object**.

### 💻 Do (30 min)
- [ ] **1.** Print a ranked leaderboard (`1. Anna – 320.00`) from `get_top_customers` (Day 7) using `enumerate`.
- [ ] **2.** Turn `product_ids = [101, 102, 103]` and `prices = [9.99, 24.50, 5.00]` into `{id: price}` with `zip`. Then try lists of different lengths, with and without `strict=True`.
- [ ] **3.** Use `any`/`all` to answer: are all order values positive? Is any order over 1000? What does `all([])` return?
- [ ] **4.** Build `{customer: round(total, 2)}` with a dict comprehension, and the unique customers with a set comprehension.
- [ ] **5.** *Bug hunt:* run this and explain what happens to `orders`:
  ```python
  cleaned = orders
  for o in cleaned:
      o["customer"] = o["customer"].upper()
  print(orders)
  ```
  Fix it in two ways: (a) build new dicts with `{**o, "customer": ...}`, (b) use `copy.deepcopy`. Then explain why `orders.copy()` alone is **not** enough.

### ✅ Check yourself (5 min)
1. `a = [1, 2]; b = a; b.append(3); print(a)` prints what?
2. What does `list(zip([1, 2, 3], ["a", "b"]))` return? What changes with `strict=True`?
3. What does a shallow copy of a list of dicts actually copy?
4. `all([])` returns what, and why is that dangerous in data validation?

<details><summary>Answers</summary>

1. `[1, 2, 3]`, because `a` and `b` are the same list.
2. `[(1, 'a'), (2, 'b')]`. The extra item is silently dropped. With `strict=True` you get a `ValueError`.
3. Only the outer list. The dicts inside are shared.
4. `True`. An **empty batch** passes an "all values valid" check, so an empty extract looks like a success. Always check the row count separately.
</details>

---

<a id="day-12"></a>
## Day 12 · Functions in depth

⏱ ~50 min · 📁 `src/day12/exercises12.py`

> 🎯 **By the end you can:** design functions with clear signatures, and split I/O from logic so the logic is easy to test.
> 💼 **At work:** "pure transformation, I/O at the edges" is how testable ETL code is structured, in plain Python and in PySpark alike.

### 📖 Learn (10 min)
- Default argument values are evaluated **once**, when the function is defined.
- `*args` collects extra positional arguments into a tuple. `**kwargs` collects extra keyword arguments into a dict.
- A bare `*` makes every parameter after it keyword-only: `def load(path, *, strict=False)`.
- Type hints: `def total(values: list[float]) -> float:`
- A **pure function** returns the same output for the same input, and has no side effects (no I/O, no changing its inputs).

### 💻 Do (35 min)
- [ ] **1.** Run this and explain the output, then fix it using `None`:
  ```python
  def add_order(order, batch=[]):
      batch.append(order)
      return batch
  print(add_order(1)); print(add_order(2))
  ```
- [ ] **2.** Write `def total(*values)` so that `total(1, 2, 3) == 6`.
- [ ] **3.** Write `def filter_orders(orders, **conditions)`. It returns the orders that match **all** the conditions, for example `filter_orders(orders, customer="Anna", status="paid")`.
- [ ] **4.** Add type hints to 3 of your functions from days 5–8.
- [ ] **5.** Refactor `process_orders` (Day 3) into `read_orders(path)` (I/O), `summarize(orders)` (**pure**) and `write_summary(summary, path)` (I/O). Which one is easiest to test, and why?

### ✅ Check yourself (5 min)
1. Why is `def f(x, items=[])` dangerous?
2. What does a bare `*` in a signature mean?
3. Why do data engineers like pure functions?
4. Does Python check type hints at runtime?

<details><summary>Answers</summary>

1. The list is created once and shared by every call, so data leaks between calls.
2. Every parameter after it must be passed by keyword, so calls like `load(path, strict=True)` stay explicit.
3. They're easy to test (no files or mocks), reproducible, and safe to rerun or parallelize.
4. No. Hints are for people and tools (mypy, your IDE). pydantic uses them at runtime (Week 5).
</details>

---

<a id="day-13"></a>
## Day 13 · 🛠 Build day: timed cleaning challenge + quiz

⏱ ~50 min · 📁 `src/day13/assessment.py`

> 🎯 **By the end you can:** clean and summarize messy records under time pressure, without help.
> 💼 **At work:** this is a staging step in miniature. Week 5 does the same with pydantic, and Week 9 does it in PySpark.

### 💻 Do (35 min, timer on, no AI, docs allowed)
```python
raw_orders = [
    {"order_id": "1", "customer": " anna ", "value": "120.50"},
    {"order_id": "2", "customer": "TOM", "value": "80"},
    {"order_id": "3", "customer": "Anna", "value": "abc"},
    {"order_id": "2", "customer": "tom", "value": "95"},     # duplicate id: keep the LAST one
    {"order_id": "4", "customer": "kate", "value": None},
    {"order_id": "5", "customer": "Kate", "value": "45.5"},
    {"order_id": "6", "customer": "anna", "value": "200"},
]
```
- [ ] **1.** `clean_orders(raw) -> list[dict]`: normalize names (`strip().title()`), convert `order_id` to int and value to float, drop invalid values, and dedupe by `order_id`, keeping the **last** occurrence.
- [ ] **2.** `customer_summary(orders, top_n) -> list[tuple]`: return `(customer, count, total, avg)` sorted by total, highest first, limited to `top_n`.
- [ ] **3.** Afterwards (untimed), ask Claude to review your code with the review prompt in the [README](README.md#-using-ai-as-a-tutor-without-letting-it-learn-for-you). Write down one thing you'll do differently next time.

### ✅ Weekly quiz
1. Which data structure would you use to check "have I seen this ID before?" for 10M IDs, and why?
2. What's the bug in `def log(msg, history=[])`?
3. `Counter` vs `defaultdict(int)`: when do you use which?
4. Why doesn't `b = a.copy()` protect nested dicts?
5. What's the complexity of sorting, and why does it matter if you sort inside a loop?

<details><summary>Answers</summary>

1. A `set`, because membership checks are `O(1)` on average.
2. The mutable default list is shared across calls.
3. `Counter` for counting things (you also get `most_common` and arithmetic). `defaultdict(int)` for summing arbitrary numbers. Both work for counting.
4. It's a shallow copy, so the inner dicts are shared.
5. `O(n log n)`. Sorting inside a loop of n iterations makes it `O(n² log n)`. Sort once, outside the loop.
</details>

---

## 🏁 End of week 1: I can…
- [ ] Count and group with `Counter` and `defaultdict` without thinking about it
- [ ] Explain why `in set` is faster than `in list`
- [ ] Spot and fix a shared-reference bug (mutable defaults, shallow copies)
- [ ] Split a script into I/O functions and pure functions

📈 Rate your confidence for Week 1 in the [progress tracker](README.md#-progress-tracker).

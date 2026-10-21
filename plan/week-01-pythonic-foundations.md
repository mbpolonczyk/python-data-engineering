# Week 1 — Pythonic data handling

You can already group, filter, sort and aggregate with plain loops (days 1–8). This week you'll learn the tools that make that code shorter and faster, and the "why" behind performance that interviewers ask about.

Code goes in `src/day9/` … `src/day13/`.

---

## Day 9 — `Counter` and `defaultdict` 🧠

**Why it matters:** in days 1–8 you wrote "if key in dict… else…" grouping logic about ten times. Senior-level Python uses the standard library for this.

**Learn (10 min)**
- `from collections import Counter, defaultdict`
- `Counter(iterable)` counts items. `.most_common(n)` returns the top n as `(item, count)` tuples.
- `defaultdict(factory)`: when you access a missing key, it calls `factory()` to create a default value (e.g. `int` → `0`, `list` → `[]`).
- Docs: https://docs.python.org/3/library/collections.html

**Do (30 min)** in `src/day9/exercises9.py`
1. Rewrite `count_occurences` from Day 5 as a one-liner with `Counter`. Print the 2 most common numbers.
2. Rewrite `calculate_customer_totals` using `defaultdict(float)`. No `if/else` allowed.
3. Using the Day 7 `orders` list, build `{customer: [order_id, ...]}` with `defaultdict(list)`.
4. Given the review texts below, find the top 3 words. Ignore case and the punctuation `.,!`
   ```python
   reviews = [
       "Great drill, great price!",
       "Drill broke after a week. Bad.",
       "Great service, fast delivery, great drill.",
   ]
   ```

**Stretch:** use `Counter` arithmetic. Given `stock_before` and `items_sold` as Counters, compute `stock_after = stock_before - items_sold`. What happens to items that drop to zero?

**Check yourself**
1. What happens when you read a missing key from `defaultdict(list)`?
2. What's the difference between `d.get("x", 0)` on a normal dict and `dd["x"]` on a `defaultdict(int)`? Why can that difference cause a bug?
3. What does `Counter("banana").most_common(1)` return?
4. Why does `defaultdict(0)` fail?

<details><summary>Answers</summary>

1. It calls `list()`, **inserts** the empty list under that key, and returns it.
2. `.get` doesn't change the dict. Reading `dd["x"]` **creates the key** as a side effect. If you only meant to check a key, you've now added an entry with value `0`. That can inflate counts or make "missing" customers appear in your output.
3. `[('a', 3)]`
4. The argument must be a *callable* (something you can call to make a new default), like `int`, `list` or `lambda: 0`. `0` isn't callable.
</details>

---

## Day 10 — Big-O and choosing data structures 🧠

**Why it matters:** "What's the complexity of this?" comes up in almost every senior interview. In data engineering, picking the wrong structure turns a 2-second job into a 2-hour one.

**Learn (15 min)**
- Big-O describes how runtime grows with input size `n`: `O(1)` constant, `O(n)` linear, `O(n log n)` (sorting), `O(n²)` (nested loops).
- `x in list` is **O(n)** because it scans every element. `x in set` and `key in dict` are **O(1) on average** because of hashing.
- Only *hashable* (immutable) things can be set members or dict keys: str, int, tuple — not list or dict.

**Do (30 min)** in `src/day10/exercises10.py`
1. Use `timeit` to measure `999_999 in big_list` vs `999_999 in big_set`, with 1,000,000 ints each:
   ```python
   import timeit
   big_list = list(range(1_000_000)); big_set = set(big_list)
   print(timeit.timeit(lambda: 999_999 in big_list, number=100))
   ```
2. Rewrite `find_duplicates` from Day 5 in **one pass**, using two sets: `seen` and `duplicates`.
3. **Two-sum (classic interview problem):** given `values = [120, 80, 200, 50, 150]` and `budget = 250`, return the indices of two orders that add up to the budget.
   - Version A: nested loops, `O(n²)`
   - Version B: one pass with a dict `{value: index}`, `O(n)`
4. Given `yesterday_customers` and `today_customers` (lists), return the customers who are new today, **keeping the order they appear in today's list**. Use a set for lookups.

**Stretch:** dedupe a list while keeping order in one line: `list(dict.fromkeys(items))`. Why does it work?

**Check yourself**
1. What's the complexity of Version A and Version B in exercise 3?
2. Why are dict and set lookups fast?
3. Can a list be a dict key? What would you use instead?
4. You need to dedupe 50 million order IDs and keep their order. How would you do it, and what's the trade-off?

<details><summary>Answers</summary>

1. A: `O(n²)`. B: `O(n)`, because each dict lookup is `O(1)`.
2. The key is hashed into a number that points almost directly to where the value is stored. There's no scanning.
3. No. Lists are mutable, so they're unhashable. Use a tuple.
4. Loop once, keeping a `seen` set and appending unseen IDs to an output list. That's `O(n)` time, but it costs `O(n)` memory for the set. If the data doesn't fit in memory, push the work to a database (`SELECT DISTINCT` / `ROW_NUMBER`) or process it in partitions.
</details>

---

## Day 11 — Unpacking, `zip`, `enumerate`, `any`/`all`, mutability 🧠

**Why it matters:** these idioms make code readable, which reviewers notice. Mutability bugs silently corrupt data, which production notices.

**Learn (10 min)**
- `for i, order in enumerate(orders, start=1)`
- `zip(a, b)` pairs up elements. `zip(a, b, strict=True)` raises an error if the lengths differ.
- `any(...)` / `all(...)` take generator expressions.
- Dict and set comprehensions: `{k: v for ...}`, `{x for ...}`
- Assignment `b = a` doesn't copy. Both names point to the **same object**.

**Do (30 min)** in `src/day11/exercises11.py`
1. Print a ranked leaderboard (`1. Anna – 320.00`) from `get_top_customers` (Day 7) using `enumerate`.
2. `product_ids = [101, 102, 103]` and `prices = [9.99, 24.50, 5.00]` → build `{id: price}` with `zip`. Then try `zip` on lists of different lengths, with and without `strict=True`.
3. With `any`/`all`: are all order values positive? Is any order over 1000? What does `all([])` return?
4. Use a dict comprehension to build `{customer: round(total, 2)}` and a set comprehension to get the unique customers.
5. **Bug hunt:**
   ```python
   cleaned = orders
   for o in cleaned:
       o["customer"] = o["customer"].upper()
   print(orders)  # What happened to the original?
   ```
   Fix it in two ways: (a) build new dicts `{**o, "customer": ...}`, (b) `copy.deepcopy`. Then explain why `orders.copy()` alone is **not** enough.

**Check yourself**
1. `a = [1, 2]; b = a; b.append(3); print(a)` → ?
2. `list(zip([1, 2, 3], ["a", "b"]))` → ? And with `strict=True`?
3. What does a shallow copy of a list of dicts actually copy?
4. `all([])` returns what, and why is that dangerous in data validation?

<details><summary>Answers</summary>

1. `[1, 2, 3]`. `a` and `b` are the same list.
2. `[(1, 'a'), (2, 'b')]`. The extra item is silently dropped. With `strict=True` you get a `ValueError`.
3. Only the outer list. The dicts inside are shared, so changing one changes it in both lists.
4. `True` ("all zero items pass"). An **empty batch** passes your "all values valid" check, so an empty extract can look successful. Check the row count separately.
</details>

---

## Day 12 — Functions in depth 🧠

**Learn (10 min)**
- Default argument values are evaluated **once**, when the function is defined.
- `*args` collects extra positional arguments into a tuple. `**kwargs` collects extra keyword arguments into a dict.
- A bare `*` in a signature makes every parameter after it keyword-only: `def load(path, *, strict=False)`
- Type hints: `def total(values: list[float]) -> float:`
- **Pure functions:** same input → same output, with no side effects (no I/O, no mutating inputs).

**Do (35 min)** in `src/day12/exercises12.py`
1. Run this and explain the output, then fix it with `None`:
   ```python
   def add_order(order, batch=[]):
       batch.append(order)
       return batch
   print(add_order(1)); print(add_order(2))
   ```
2. `def total(*values)` → `total(1, 2, 3) == 6`.
3. `def filter_orders(orders, **conditions)` returns the orders matching **all** the conditions, e.g. `filter_orders(orders, customer="Anna", status="paid")`.
4. Add type hints to 3 of your functions from days 5–8.
5. **Refactor `process_orders` (Day 3)** into three functions: `read_orders(path)` (I/O), `summarize(orders)` (**pure**), and `write_summary(summary, path)` (I/O). Which one is easiest to test, and why?

**Check yourself**
1. Why is `def f(x, items=[])` dangerous?
2. What does a bare `*` in a signature mean?
3. Why do data engineers like pure functions?
4. Does Python check type hints at runtime?

<details><summary>Answers</summary>

1. The list is created once and shared by every call, so data leaks between calls.
2. Every parameter after it must be passed by keyword. That makes calls like `load(path, strict=True)` explicit.
3. They're easy to test (no files or mocks needed), reproducible, safe to rerun and safe to parallelize.
4. No. They're for humans and tools (mypy, IDEs). pydantic is a library that *uses* them at runtime (Week 5).
</details>

---

## Day 13 — Week 1 review: timed mini assessment 🔁

**Do (35 min, timer on, no AI, docs allowed)** in `src/day13/assessment.py`

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
1. `clean_orders(raw) -> list[dict]`: normalize names (`strip().title()`), convert `order_id` to int and value to float, drop invalid values, and dedupe by `order_id` keeping the **last** occurrence.
2. `customer_summary(orders, top_n) -> list[tuple]`: return `(customer, count, total, avg)` sorted by total, highest first, limited to `top_n`.
3. Afterwards (untimed): ask Claude to review the code using the review prompt in the [plan README](README.md). Write down 1 thing you'll do differently next time.

**Weekly quiz** (answer before you open the answers)
1. Which data structure would you use to check "have I seen this ID before?" for 10M IDs, and why?
2. What's the bug: `def log(msg, history=[])`?
3. `Counter` vs `defaultdict(int)`: when do you use which?
4. Why does `b = a.copy()` not protect nested dicts?
5. What's the complexity of sorting, and why does it matter if you sort inside a loop?

<details><summary>Answers</summary>

1. A `set`, because membership checks are `O(1)` on average.
2. The mutable default list is shared across calls.
3. `Counter` when you're counting things (it also gives you `most_common` and arithmetic). `defaultdict(int)` when you're summing or accumulating arbitrary numbers. Both work for counting.
4. It's a shallow copy. The inner objects are shared.
5. `O(n log n)`. Sorting inside a loop of n iterations makes the whole thing `O(n² log n)`. Sort once, outside the loop.
</details>

📝 Fill in your confidence log in the README.

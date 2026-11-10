# Complexity

How the work grows as the data grows, and picking the data structure that keeps it small.

### Big-O notation
**What:** A way to say how much more work your code does when the data gets bigger. `n` = number of items.
```python
"Anna" in {"Anna", "Tom"}   # O(1): same work for 10 or 10M customers
307 in [101, 205, 307]      # O(n): 10× more orders → 10× more work
# for a in orders: for b in orders: ...   # O(n²): 10× more orders → 100× more work
```
| Big-O | 10× more data means | Example |
|---|---|---|
| O(1) | same work | `in set`, `dict[key]` |
| O(n) | 10× work | `in list`, one `for` loop |
| O(n log n) | a bit more than 10× | `sorted()` |
| O(n²) | 100× work | loop inside a loop |

**Gotcha:** O(n²) looks fine on 100 test rows and dies on 1M production rows: 1,000,000,000,000 steps.
**SQL/Spark twin:** a join without a usable key is the SQL version of a nested loop.
**Interview line:** "This is O(n²) because of the nested loop; I can get it to O(n) by keeping a set of what I've seen."
**Related:** [List vs set vs dict](#list-vs-set-vs-dict), [Hashing and hashable types](#hashing-and-hashable-types)
_Learned: Day 10 · 2026-11-10_

### List vs set vs dict
**What:** Three containers, each built for a different question. List = pile of receipts (keeps order and duplicates, searches one by one). Set = guest list at the door ("is X here?" instantly, no duplicates). Dict = warehouse locator (key → value, instant lookup).
```python
order_ids = [101, 205, 307, 205]       # list: order + duplicates kept
customers = {"Anna", "Tom", "Anna"}    # set: {'Anna', 'Tom'}
shelf_of = {"DRILL-01": "A3"}          # dict: shelf_of["DRILL-01"] -> 'A3'
```
- "Have I seen this?" → **set** · "Have I seen it, and what goes with it?" → **dict** · "Keep order / duplicates" → **list**

**Gotcha:** Converting a list to a set costs one pass, O(n). It pays off when you look things up many times, not for a single check.
**SQL/Spark twin:** a set lookup is like checking against an indexed column; a list scan is a full table scan.
**Interview line:** "I'd convert the list to a set once. That's O(n), but then each of the 10,000 lookups is O(1) instead of O(n)."
**Related:** [Big-O notation](#big-o-notation), [The `seen` set pattern](#the-seen-set-pattern)
_Learned: Day 10 · 2026-11-10_

### Hashing and hashable types
**What:** A set or dict turns each value into a number (a **hash**) that works like a shelf address, so Python jumps straight to it instead of searching. That's why lookups are O(1).
```python
hash("DRILL-01")             # some int: the "shelf address"
{("Anna", 2026): 320}        # tuple as key: OK
# {["Anna", 2026]: 320}      # TypeError: unhashable type: 'list'
```
**Gotcha:** Only values that can't change can be hashed: `str`, `int`, `float`, `tuple`. A `list` or `dict` can't be a set member or dict key; use a `tuple` instead.
**Interview line:** "Dict and set lookups are O(1) on average because the key is hashed straight to its slot — no scanning."
**Related:** [List vs set vs dict](#list-vs-set-vs-dict)
_Learned: Day 10 · 2026-11-10_

### The `seen` set pattern
**What:** Walk the data once and keep a set of what you've already met. Each "have I seen it?" check is O(1), so the whole thing is O(n).
```python
seen = set()
for sku in ["DRILL-01", "SAW-02", "DRILL-01"]:
    if sku in seen:
        print(sku, "is a repeat")   # DRILL-01 is a repeat
    else:
        seen.add(sku)
```
**Gotcha:** Fast, but `seen` holds every unique value in memory, so 50M IDs need a lot of RAM.
**SQL/Spark twin:** `ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) = 1` · `df.dropDuplicates(["id"])`
**Interview line:** "For one-pass dedupe I keep a `seen` set: O(n) time, O(n) memory."
**Related:** [List vs set vs dict](#list-vs-set-vs-dict), [`Counter`](collections.md#counter)
_Learned: Day 10 · 2026-11-10_

### `timeit.timeit`
**What:** A stopwatch for code: runs a small piece of code `number` times and returns the **total seconds**.
```python
import timeit
big_list = list(range(1_000_000)); big_set = set(big_list)
timeit.timeit(lambda: 999_999 in big_list, number=100)   # slow: scans 1M items each time
timeit.timeit(lambda: 999_999 in big_set, number=100)    # near zero
```
**Gotcha:** The result is the total for all runs, not per run. And `999_999` is the last item on purpose: the worst case for a list.
**Interview line:** "Before optimising, I measure: `timeit` for small snippets, a profiler for whole pipelines."
**Related:** [`lambda`](functions.md#lambda), [Big-O notation](#big-o-notation)
_Learned: Day 10 · 2026-11-10_

# Generators

Lazy iteration: producing values one at a time instead of building whole lists in memory.

### Generator expression
**What:** A comprehension written in `( )` instead of `[ ]`. It produces values one at a time, on demand, instead of building a whole list in memory.
```python
total = sum(o["value"] for o in orders)       # generator: flat memory use
total = sum([o["value"] for o in orders])     # list: builds the full list first
```
**Gotcha:** A generator can be consumed only **once**, and it has no `len()` and no indexing. Loop over it a second time and you get nothing.
**SQL/Spark twin:** Spark is lazy in the same way: transformations do nothing until an action (`count`, `write`) pulls the data through.
**Interview line:** "If I only loop over the result once, for example with `sum`, `max`, `any` or a `for` loop, I use a generator expression. It keeps memory flat even on millions of rows."
**Example (quiz, Day 10):** same result, different cost:
```python
orders = [{"order_id": 1, "value": 120}, {"order_id": 2, "value": 80}, {"order_id": 3, "value": 200}]
a = sum([o["value"] for o in orders])  # 400, but the full list sits in memory first
b = sum(o["value"] for o in orders)    # 400, values made one at a time, used, thrown away
```
"The list comprehension builds every value in memory before `sum` runs. The generator expression produces them one at a time, so memory stays flat. That matters when you stream a 10 GB CSV or a big API export row by row: the list version can run out of memory, the generator version won't."
**Related:** [Counter](collections.md#counter)
_Learned: Day 8 · 2026-10-13 · Seen again: Day 9, Day 10_

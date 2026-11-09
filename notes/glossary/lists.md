# Lists

Working with lists: sorting, copying, changing in place.

### `sorted()` vs `list.sort()`
**What:** `sorted(x)` returns a **new** sorted list and leaves `x` unchanged. `x.sort()` rearranges the same list **in place** and returns `None`.
```python
orders = [120, 80, 200]
new = sorted(orders)    # new = [80, 120, 200], orders unchanged
orders.sort()           # orders = [80, 120, 200], returns None
```
**Gotcha:** `orders = orders.sort()` sets `orders` to `None`. In-place methods (`.sort()`, `.append()`, `dict.update()`) return `None`. Also, every other name that points to the same list sees the change.
**SQL/Spark twin:** `ORDER BY` · `df.orderBy("value")`. Spark DataFrames are immutable, so it always works like `sorted()`.
**Interview line:** "In pipelines I prefer `sorted()`: it doesn't mutate the input, so one step can't break another. `.sort()` only saves memory on lists I own."
**Related:** [generator expression](generators.md#generator-expression)
_Learned: Day 8 · 2026-10-13 · Seen again: Day 9_

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
_Learned: Day 8 · 2026-10-13 · Seen again: Day 9 (`x = x.append(...)` stored None)_

### `.append()` vs `.extend()`
**What:** `.append(x)` adds **one** item to the end of a list. `.extend(iterable)` adds **every item** of another list or iterable. Both change the list in place and return `None`.
```python
ids = [1]
ids.append(3)        # [1, 3]
ids.extend([4, 5])   # [1, 3, 4, 5]
ids += [6]           # same as .extend → [1, 3, 4, 5, 6]
```
**Gotcha:** `ids += 7` raises `TypeError: 'int' object is not iterable`, because `+=` on a list means *extend*. `ids.append([4, 5])` adds **one** nested list: `[1, [4, 5]]`. And `ids = ids.append(3)` sets `ids` to `None`.
**SQL/Spark twin:** `collect_list` builds lists per group. `F.flatten` / `explode` are related to extend.
**Interview line:** "`append` adds one element, `extend` concatenates an iterable. Both mutate in place and return None."
**Related:** [`sorted()` vs `list.sort()`](#sorted-vs-listsort), [defaultdict](collections.md#defaultdict)
_Learned: Day 9 · 2026-11-09_

# Collections

Specialised dicts from the `collections` module that remove "if the key is missing…" boilerplate.

### `Counter`
**What:** A dict that counts how many times each item appears in an iterable. `.most_common(n)` returns the top n as `(item, count)` tuples, highest first.
```python
from collections import Counter
c = Counter(["drills", "saws", "drills"])   # Counter({'drills': 2, 'saws': 1})
c.most_common(1)                            # [('drills', 2)]
c["hammers"]                                # 0, no KeyError, and the key is NOT added
```
**Gotcha:** `.most_common()` without `n` returns *all* items sorted. `c1 - c2` silently drops counts that fall to zero or below.
**SQL/Spark twin:** `SELECT x, COUNT(*) ... GROUP BY x ORDER BY 2 DESC LIMIT n` · `df.groupBy("x").count().orderBy(desc("count")).limit(n)`
**Interview line:** "For top-N counts I use `Counter(...).most_common(n)`: one O(n) pass, no hand-written loop. With huge files I stream lines and call `.update()`."
**Related:** [defaultdict](#defaultdict), [generator expression](generators.md#generator-expression)
_Learned: Day 9 · 2026-11-09_

### `defaultdict`
**What:** A dict that calls a *factory* (`int`, `float`, `list`, `set`, a `lambda`) to create a starting value whenever a missing key is read.
```python
from collections import defaultdict
skus = defaultdict(list)
skus["Anna"].append("D-100")   # no "if key not in" needed
dict(skus)                     # {'Anna': ['D-100']}
```
**Gotcha:** Just *reading* `dd["x"]` **inserts** the key. Use `"x" in dd` or `dd.get("x")` to check without creating it. `defaultdict(0)` fails because the factory must be callable.
**SQL/Spark twin:** `defaultdict(float)` + `+=` ≈ `SUM(value) GROUP BY key` · `defaultdict(list)` ≈ `collect_list` / `ARRAY_AGG`
**Interview line:** "I use `defaultdict(list)` to group and `defaultdict(float)` to sum per key, and I convert to a plain `dict` before returning, so nobody creates keys by accident."
**Related:** [Counter](#counter), [dict.get and KeyError](dicts.md#dictget-and-keyerror)
_Learned: Day 9 · 2026-11-09_

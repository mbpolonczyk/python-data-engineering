# Functions

How to write functions that behave predictably in a pipeline.

### Pure function (create state inside)
**What:** A function whose result depends **only on its inputs** and that changes nothing outside itself. So anything it builds up (a dict, list or counter) is created *inside* the function, and each call starts fresh.
```python
from collections import defaultdict
totals = defaultdict(float)              # ❌ created once, shared by every call
def bad_totals(orders):
    for o in orders:
        totals[o["customer"]] += o["value"]
    return dict(totals)

def good_totals(orders):
    totals = defaultdict(float)          # ✅ fresh on every call
    for o in orders:
        totals[o["customer"]] += o["value"]
    return dict(totals)

orders = [{"customer": "Anna", "value": 120}]
bad_totals(orders); bad_totals(orders)   # {'Anna': 240.0}, doubled on the 2nd call
good_totals(orders); good_totals(orders) # {'Anna': 120.0}, same every time
```
**Gotcha:** The sneakier version is a mutable default argument: `def f(orders, totals={})`. The `{}` is created only once, so it's shared between calls too (Day 12).
**SQL/Spark twin:** This is the same idea as an **idempotent** job: re-running yesterday's load must not double the revenue.
**Interview line:** "I keep transformations pure: state is created inside the function and the result depends only on the input. That makes them easy to test and safe to re-run."
**Related:** [defaultdict](collections.md#defaultdict)
_Learned: Day 9 · 2026-11-09_

### Helper function (extract a step)
**What:** Move one self-contained step, like a long chain of operations, into a small named function, so the main code says *what* happens and the helper hides *how*.
```python
import re
def to_words(text):
    """Turn a sentence into a list of clean, lowercase words."""
    return re.findall(r"[\w']+", text.lower())

to_words("Great drill, great price!")   # ['great', 'drill', 'great', 'price']
```
**Gotcha:** Give it one job and a name that says what it returns. Keep it pure, with no prints or global state, so you can unit-test it alone with edge cases (`""`, `"Bad!!"`).
**Interview line:** "When a line gets long I pull it into a helper, so it's readable, reusable and testable on its own."
**Related:** [Pure function](#pure-function-create-state-inside), [`re.findall`](regex.md#refindall-and-w)
_Learned: Day 9 · 2026-11-09_

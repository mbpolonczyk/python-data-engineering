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
**Related:** [Counter](collections.md#counter)
_Learned: Day 8 · 2026-10-13 · Seen again: Day 9_

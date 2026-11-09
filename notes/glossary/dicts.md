# Dicts

Reading, writing and safely looking up keys in plain dictionaries.

### `dict.get()` and `KeyError`
**What:** `d["x"]` raises `KeyError` when `"x"` is missing. `d.get("x", default)` returns the default (or `None`) instead, and doesn't change the dict.
```python
totals = {"Anna": 320}
totals["Zoe"]           # KeyError: 'Zoe'
totals.get("Zoe", 0)    # 0
"Zoe" in totals         # False
```
**Gotcha:** `.get()` hides typos and missing data. Use `d[key]` when a missing key *should* fail loudly, for example a required column.
**SQL/Spark twin:** `COALESCE(col, 0)` · `F.coalesce(col, F.lit(0))`
**Interview line:** "I use `.get(key, default)` for optional fields and `d[key]` for required ones, so bad data fails fast instead of becoming silent zeros."
**Related:** [defaultdict](collections.md#defaultdict)
_Learned: Day 5 · Seen again: Day 9_

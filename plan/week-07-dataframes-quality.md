# Week 7 · DataFrames and data quality

**Phase 3 — ETL transformations** · Days 39–43
[← Week 6](week-06-sql-duckdb.md) · [Plan overview](README.md) · [Week 8 →](week-08-pyspark-fundamentals.md)

> **This week's outcome:** you transform data with pandas and polars as confidently as with SQL, you know the traps that silently corrupt DataFrames, and your pipeline refuses to publish data that fails its quality checks.
>
> **Project milestone:** `shopflow` runs data-quality checks after staging and after the marts, and only publishes the marts to `data/marts/` when every `error` check passes. **This ends Phase 3.**

| Day | Topic | Time |
|---|---|---|
| 39 | pandas core transformations and method chaining | ~45 min |
| 40 | pandas pitfalls: dtypes, nulls, copies, timezones, merges | ~50 min |
| 41 | polars: expressions and lazy frames | ~45 min |
| 42 | Data-quality checks as code | ~55 min |
| 43 | 🛠 Build day: quality gate + SQL vs pandas vs polars + quiz | ~60 min |

All this week's practice uses the same small dataset. Put it in `src/day39/data.py` and import it on later days:
```python
import pandas as pd
orders = pd.DataFrame({
    "order_id":    [1, 2, 3, 4, 5, 6],
    "customer_id": [7, 8, 7, 9, 8, 7],
    "product_id":  [101, 102, 101, 103, 102, 103],
    "quantity":    [2, 1, 1, 3, 2, 1],
    "unit_price":  [10.0, 25.0, 10.0, 5.0, 25.0, 5.0],
    "status":      ["paid", "paid", "cancelled", "paid", "paid", "paid"],
    "order_date":  pd.to_datetime(["2026-03-01", "2026-03-01", "2026-03-02",
                                   "2026-03-02", "2026-03-03", "2026-03-03"]),
})
products = pd.DataFrame({"product_id": [101, 102, 103], "category": ["tools", "garden", "tools"]})
```

---

<a id="day-39"></a>
## Day 39 · pandas core transformations and method chaining

⏱ ~45 min · 📁 `src/day39/exercises39.py`

> 🎯 **By the end you can:** select, filter, add columns, aggregate, join and pivot in pandas, written as one readable chain.
> 💼 **At work:** almost every Python data job uses pandas somewhere, even if the warehouse runs on SQL.

### 📖 Learn (10 min)
- `df[["a", "b"]]` selects columns. `df.loc[mask, cols]` filters rows and picks columns. `df.query("status == 'paid'")` is a readable filter.
- `df.assign(revenue=lambda d: d.quantity * d.unit_price)` adds a column and returns a **new** DataFrame.
- `df.groupby("order_date", as_index=False).agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))`: named aggregations.
- `pd.merge(left, right, on="product_id", how="left", validate="many_to_one")`.
- `df.pivot_table(index=..., columns=..., values=..., aggfunc="sum", fill_value=0)`.
- **Method chaining:** wrap the chain in `( ... )` with one step per line. It reads like a SQL query.
- Docs: https://pandas.pydata.org/docs/user_guide/10min.html

### 💻 Do (30 min)
- [ ] **1.** In `shopflow/`, `uv add pandas` if you haven't yet. Paid orders only, with a `revenue` column, using `query` and `assign` in one chain.
- [ ] **2.** Daily revenue with named aggregations. Expected: 03-01 → 45.0, 03-02 → 15.0, 03-03 → 55.0.
- [ ] **3.** Customer stats: orders and total spend per customer. Expected: 7 → 2 orders / 25.0, 8 → 2 / 75.0, 9 → 1 / 15.0.
- [ ] **4.** Merge in `products` with `validate="many_to_one"`, then a pivot: dates as rows, categories as columns, revenue as values, `fill_value=0`. Expected tools column: 20, 15, 5.
- [ ] **5.** Load your real `mart_daily_revenue` with `con.sql("SELECT * FROM mart_daily_revenue").df()` and rebuild it in pandas from `stg_erp__orders`. Do the totals match exactly?
- ⭐ *Stretch:* move the revenue step into a function and use it with `.pipe(add_revenue)` in the chain.

### ✅ Check yourself (5 min)
1. Series vs DataFrame?
2. Why named aggregations (`revenue=("revenue", "sum")`)?
3. What do `how="inner"` and `how="left"` do to the row count?
4. Why is a method chain easier to review than ten reassignments of `df`?

<details><summary>Answers</summary>

1. A Series is one labelled column. A DataFrame is a table of Series sharing an index.
2. You choose clear output names in one step and avoid multi-level column headers.
3. Inner keeps only matching rows, so rows can disappear. Left keeps every left row (unmatched get missing values). Both can **multiply** rows if the right key isn't unique.
4. Each step is one line with no temporary names, the original stays unchanged, and it reads top to bottom like a pipeline, much like a CTE.
</details>

---

<a id="day-40"></a>
## Day 40 · pandas pitfalls: dtypes, nulls, copies, timezones, merges

⏱ ~50 min · 📁 `src/day40/exercises40.py`

> 🎯 **By the end you can:** spot and fix the pandas mistakes that silently corrupt numbers.
> 💼 **At work:** these bugs don't crash. They just make a report wrong, and nobody notices for weeks.

### 📖 Learn (15 min)
- Check your version with `pd.__version__`. **pandas 3** (Jan 2026) changed two things: text columns get a dedicated `str` dtype (2.x used `object`), and Copy-on-Write is always on.
- An int column with a missing value becomes `float64`. Nullable `Int64` (capital I) keeps ints and shows `<NA>`.
- `np.nan == np.nan` is `False`. Always test with `.isna()` / `pd.isna()`.
- **Chained assignment** `df[mask]["col"] = x` changes a temporary copy. In pandas 3 it never works; in 2.x you get a `SettingWithCopyWarning`. Use `df.loc[mask, "col"] = x`.
- Datetimes: `pd.to_datetime(s, utc=True)` makes everything timezone-aware UTC. `tz_localize` **attaches** a zone to naive times, `tz_convert` **converts** aware times. Comparing naive with aware raises `TypeError`.
- `merge(..., validate="one_to_one")` or `"many_to_one"` raises `MergeError` if keys aren't unique.
- Docs: https://pandas.pydata.org/docs/user_guide/copy_on_write.html

### 💻 Do (30 min)
- [ ] **1.** *Predict, then run:* the dtype of each Series. Then convert `b` to `Int64` and `c` to numbers with `pd.to_numeric(c, errors="coerce")`. How many NaNs?
  ```python
  a = pd.Series(["anna", None, "tom"]); b = pd.Series([1, None, 3]); c = pd.Series(["12.5", "abc", "7"])
  ```
- [ ] **2.** *Bug hunt:* run this on the shared `orders` and explain what happens. Fix it with `.loc`.
  ```python
  orders[orders["unit_price"] > 20]["status"] = "big"
  print(orders["status"].tolist())
  ```
- [ ] **3.** Timezones: parse `["2026-03-29T01:30:00+01:00", "2026-03-29T00:45:00Z"]` with `utc=True` and sort. Then convert to `Europe/Warsaw`. Which order happened first, and on which local date? (This is the night clocks change.)
- [ ] **4.** *Merge explosion:* add a second row for product 101 to `products` (a "duplicate from the API"). Merge with `orders` and compare row counts and total revenue. Then add `validate="many_to_one"` and read the error.
- [ ] **5.** `orders.merge(products, on="product_id", validate="one_to_one")` fails even with clean products. Why? Which `validate` value is correct here?
- ⭐ *Stretch:* `df.memory_usage(deep=True)` before and after `status.astype("category")` on 1M generated rows.

### ✅ Check yourself (5 min)
1. Why does an int column turn into float when a value is missing, and what's the fix?
2. What does `df[df.x > 1]["y"] = 0` do in pandas 3?
3. `tz_localize` vs `tz_convert`?
4. A merge takes 1,000 rows to 1,350. What happened, and how do you prevent it?

<details><summary>Answers</summary>

1. NumPy ints can't hold a missing value, so pandas switches to float and NaN. Use the nullable `Int64` dtype.
2. Nothing to `df`. It sets values on a temporary copy (pandas warns with `ChainedAssignmentError`). Write `df.loc[df.x > 1, "y"] = 0`.
3. `tz_localize` says "these naive times are in this zone" (no clock change). `tz_convert` changes aware times to another zone (same instant, different clock time).
4. The right side has duplicate join keys, so left rows are repeated (fan-out). Dedupe the right side and use `validate="many_to_one"` so it fails loudly next time.
</details>

---

<a id="day-41"></a>
## Day 41 · polars: expressions and lazy frames

⏱ ~45 min · 📁 `src/day41/exercises41.py`

> 🎯 **By the end you can:** transform data with polars expressions, and explain lazy evaluation and query plans.
> 💼 **At work:** polars is fast on one machine, and its lazy mode is **the same mental model as Spark**, which you start next week.

### 📖 Learn (10 min)
- Everything is an **expression**: `pl.col("quantity") * pl.col("unit_price")`. Use them in `select`, `with_columns`, `filter`, `group_by(...).agg(...)`.
- **Eager:** `pl.read_parquet` and `pl.DataFrame` run each step immediately. **Lazy:** `pl.scan_parquet` or `df.lazy()` builds a **plan**; nothing runs until `.collect()`.
- The optimizer rewrites the plan: **predicate pushdown** (filter while reading) and **projection pushdown** (read only needed columns). See it with `.explain()`.
- Spark works the same way: transformations build a plan, and an **action** (`count`, `show`, `write`) runs it. `.collect()` is polars' action.
- Docs: https://docs.pola.rs/user-guide/concepts/lazy-api/

### 💻 Do (30 min)
- [ ] **1.** `uv add polars pyarrow`. Convert the shared data with `pl.from_pandas(orders)` and rebuild Day 39's daily revenue and customer stats with expressions. Same expected numbers.
- [ ] **2.** Generate 2M orders (numpy random ints for ids and quantities, a few dates and statuses) and write them to `data/practice/orders.parquet` with `write_parquet`.
- [ ] **3.** Lazy query: `scan_parquet` → filter paid → `with_columns` revenue → `group_by("order_date")` → `agg` → `sort`. Print `.explain()` **before** collecting. Find the filter and the column selection inside the scan step.
- [ ] **4.** Time the same query in pandas (`pd.read_parquet` + chain) and polars lazy (`time.perf_counter`). Write down both numbers.
- [ ] **5.** *Predict:* if you add `print("built")` after building the lazy query, but never call `.collect()`, how much of the Parquet file has been read?
- ⭐ *Stretch:* polars has its own `pl.SQLContext`. Run the same query as SQL and compare the plans.

### ✅ Check yourself (5 min)
1. Eager vs lazy execution?
2. What are predicate and projection pushdown, and why do they matter?
3. How does polars' `.collect()` relate to a Spark action?
4. When would you still choose pandas?

<details><summary>Answers</summary>

1. Eager runs each step at once. Lazy records the steps, optimizes the whole plan, then runs it when asked.
2. Filtering rows and selecting columns during the file read, so far less data is read and held in memory.
3. Same idea: nothing executes until you ask for a result. In Spark, `count()`, `show()` and `write` are actions; `filter` and `select` only extend the plan.
4. When a library expects pandas, for existing team code, or for small data where speed doesn't matter.
</details>

---

<a id="day-42"></a>
## Day 42 · Data-quality checks as code

⏱ ~55 min · 📁 `shopflow/src/shopflow/quality/checks.py`, `shopflow/tests/test_checks.py`

> 🎯 **By the end you can:** write reusable checks that decide whether data is good enough to publish.
> 💼 **At work:** "how do you know your data is correct?" is a senior interview question. "We have checks that block the load" is the answer.

### 📖 Learn (10 min)
- Check types: **volume** (row count), **uniqueness** (keys), **completeness** (not null), **validity** (accepted values, ranges), **freshness** (latest timestamp), **reconciliation** (totals match between layers).
- **Severity:** `error` stops the pipeline. `warn` logs and alerts, but data still flows.
- Validation (Week 5) checks **records**. Quality checks look at whole **tables**: duplicates, missing days, totals.
- Tools that do this at scale: Great Expectations, Soda, pandera (DataFrames), dbt tests. Today you build a small version yourself to understand them.
- Table and column names can't be `?` parameters. They come from your code, never from users.

### 💻 Do (40 min)
- [ ] **1.** `Severity(StrEnum)` with `ERROR` and `WARN`, and `@dataclass(frozen=True) CheckResult(name, table, passed, severity, details)`.
- [ ] **2.** Each check runs one SQL query on DuckDB and returns a `CheckResult`: `check_row_count(con, table, min_rows)`, `check_unique(con, table, key)`, `check_not_null(con, table, column)`, `check_accepted_values(con, table, column, values)`, `check_range(con, table, column, min_value, max_value)`.
- [ ] **3.** `check_freshness(con, table, ts_column, max_age)`: fails if the newest timestamp is older than `max_age`. `check_reconciliation(con, name, sql_a, sql_b, tolerance)`: e.g. paid revenue in `stg_erp__orders` equals total revenue in `mart_daily_revenue`.
- [ ] **4.** `run_checks(checks) -> list[CheckResult]`: log each result and raise `DataQualityError` listing every failed `error` check (not just the first).
- [ ] **5.** Tests with a tiny in-memory table: one passing case and one failing case per check. Include an **empty** table in `check_not_null`. *Predict:* does it pass? Should it?
- [ ] **6.** 📘 Playbook §6: your checks per layer and how you chose `error` vs `warn`.

### ✅ Check yourself (5 min)
1. Give one check for raw, one for staging and one for marts.
2. `warn` vs `error`: how do you decide?
3. Why does a not-null check pass on an empty table, and what protects you?
4. Pydantic already validated every record. Why do you still need table checks?

<details><summary>Answers</summary>

1. Raw: row count above zero and close to the last run. Staging: primary key unique, required columns not null. Marts: revenue not negative, and the total reconciles with staging.
2. `error` when publishing would be wrong or misleading (duplicate keys, empty load, totals don't match). `warn` when it's suspicious but usable (fewer rows than usual, a new category).
3. Zero rows means zero nulls, so it passes. A separate row-count check catches the empty table (the same `all([])` trap from Day 11).
4. Record validation can't see problems across rows: duplicates, missing days, a join that doubled revenue, or yesterday's file loaded twice.
</details>

---

<a id="day-43"></a>
## Day 43 · 🛠 Build day: quality gate + SQL vs pandas vs polars + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/transform/run.py`, `src/day43/compare.py`

> 🎯 **By the end you can:** stop bad data before it's published, and do the same transformation in three tools.
> 💼 **At work:** this is the **write-audit-publish** pattern: build, check, and only then make it visible.

### 💻 Do (45 min)
- [ ] **1.** In `run_transform`: staging → **staging checks** → marts → **mart checks** → publish (the Parquet export from Day 38). If an `error` check fails, nothing is exported and yesterday's files stay in `data/marts/`.
- [ ] **2.** Save every `CheckResult` to a `dq_results` table with a `run_id` and a timestamp, so you can see trends.
- [ ] **3.** Test the gate: a fixture with a duplicate order (after dedupe it must pass) and one with a negative amount (it must fail and publish nothing).
- [ ] **4.** In `src/day43/compare.py`, compute **paid revenue per day and category** from the shared data three ways: DuckDB SQL (on the DataFrames), pandas and polars. Convert all three to pandas, sort, reset the index, and assert they're equal with `pd.testing.assert_frame_equal(..., check_dtype=False)`.
- [ ] **5.** Write three sentences in `compare.py`: which version was easiest to read, which was easiest to test, and which you'd pick for `shopflow`.
- [ ] **6.** 📘 Finish Playbook §6. Commit.

### ✅ Weekly quiz
1. SQL, pandas or polars: one sentence each on when to use it.
2. What does `validate="many_to_one"` protect you from?
3. *Explain out loud:* what is lazy evaluation, and why does it make queries faster?
4. A check fails at 3 a.m. What should the pipeline do with the data, and what should it do about people?
5. Name six kinds of data-quality checks.

<details><summary>Answers</summary>

1. (Yours.) SQL for set-based transformations in the warehouse that analysts can read. pandas for small to medium data and its huge ecosystem. polars for fast single-machine work on bigger data.
2. Fan-out: duplicate keys on the right side silently multiplying rows (and revenue). The merge fails instead.
3. (Yours.) Steps are recorded as a plan instead of running one by one. Before running, the optimizer sees the whole query, so it can filter and drop columns while reading and skip work it doesn't need.
4. Don't publish: keep the last good version of the marts. Alert the on-call person with a clear message: which check, which table, the numbers, and the run ID.
5. Volume, uniqueness, completeness (not null), validity (accepted values, ranges), freshness, reconciliation.
</details>

> 🎉 **Phase 3 done.** You can transform data with SQL, pandas and polars, load it idempotently and protect it with checks. **Next: PySpark.** Same ideas (lazy plans, layers, idempotent loads, checks), but on data too big for one machine.

---

## 🏁 End of week 7: I can…
- [ ] Write pandas transformations as a readable chain
- [ ] Avoid dtype, null, copy, timezone and merge-explosion bugs
- [ ] Use polars lazy frames and read a query plan
- [ ] Write data-quality checks that block a bad load

📈 Rate your confidence for Week 7 in the [progress tracker](README.md#-progress-tracker).

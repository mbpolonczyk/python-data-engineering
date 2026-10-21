# Week 7 — DataFrames and data quality

Nearly every data engineering job ad mentions pandas. Polars is the fast modern alternative. You'll learn both, and when to use SQL instead. Then you'll add data-quality checks, which is where senior engineers stand out.

---

## Day 39 — pandas core 🧠

**Learn (15 min)**
- A `DataFrame` is a table. A `Series` is one column.
- Selecting: `df["col"]`, `df[["a", "b"]]`, `df.loc[mask, cols]`
- `df.groupby("customer").agg(total=("value", "sum"), n=("value", "size"))`
- `pd.merge(a, b, on="id", how="left", validate="many_to_one")`
- `sort_values`, `head`, `assign`, `query`

**Do (35 min)** in `shopflow/notebooks/` or `src/day39/`
1. `uv add pandas`. Load `stg_cart_items` and `stg_products` from DuckDB with `con.sql("...").df()`.
2. Redo your Day 1 analysis in pandas: total revenue, average cart value, top 3 users by spend.
3. Merge items with products to get the category. Use `validate="many_to_one"`. Then deliberately create a duplicate product row and watch it fail.
4. Revenue per category, sorted. Check that it matches your SQL mart **exactly**.

**Check yourself**
1. Series vs DataFrame?
2. Why use named aggregations (`total=("value", "sum")`)?
3. What do `how="inner"` and `how="left"` do to row counts?
4. Why `validate="many_to_one"` in merges?

<details><summary>Answers</summary>

1. A Series is a single labelled column. A DataFrame is a table of Series sharing an index.
2. You get clear output column names in one step, and no messy multi-level columns.
3. Inner keeps only matching rows (rows can disappear). Left keeps every left row (unmatched rows get NaN). Both can **multiply** rows if the right key isn't unique.
4. It fails loudly if the right side has duplicate keys, catching the "revenue suddenly doubled" fan-out bug.
</details>

---

## Day 40 — pandas pitfalls 🧠

**Do (40 min)** in `src/day40/exercises40.py`
1. **dtypes:** read a CSV where `value` contains `"abc"` → it becomes `object`. Fix it with `pd.to_numeric(errors="coerce")`. Count the NaNs.
2. **Nullable ints:** an int column with one missing value becomes `float64`. Fix it with `.astype("Int64")`.
3. **Speed:** on 1M generated rows, compute `value * 1.23` with (a) `iterrows`, (b) `apply`, (c) a vectorized expression. Time them.
4. **Chained assignment:** `df[df.value > 100]["flag"] = True` doesn't work as expected. Use `df.loc[df.value > 100, "flag"] = True`. (pandas 3 uses Copy-on-Write: read the warning or docs.)
5. **Memory:** `df.memory_usage(deep=True)` before and after converting `customer` to `category` dtype.

**Check yourself**
1. Why is vectorized code so much faster than `apply`/`iterrows`?
2. What does `np.nan == np.nan` return? How do you check for nulls?
3. Why does an int column become float when there's a missing value?
4. When does the `category` dtype help?

<details><summary>Answers</summary>

1. The loop runs in optimized C over whole arrays, instead of calling a Python function once per row.
2. `False`. Use `.isna()` / `pd.isna()`.
3. The classic NumPy int can't represent a missing value, so pandas falls back to float NaN. `Int64` (capital I) is the nullable integer type.
4. Columns with few unique values repeated many times (country, status): big memory savings and faster groupbys.
</details>

---

## Day 41 — Polars 🧠

**Learn (10 min)**
- Polars is built in Rust, multi-threaded, and uses an **expression** API: `pl.col("value").sum()`
- **Lazy mode:** `pl.scan_parquet(...)` builds a query plan, `.collect()` runs it. The optimizer pushes filters and column selection down to the file read.
- Docs: https://docs.pola.rs/user-guide/getting-started/

**Do (35 min)**
1. `uv add polars`
2. Redo Day 39's category revenue in polars (eager).
3. Generate 5M fake orders → write them to Parquet → run the same aggregation with pandas (`read_parquet`) and with polars lazy (`scan_parquet().filter().group_by().agg().collect()`). Time both.
4. Print `lazy_query.explain()` and find where the filter was pushed down.

**Check yourself**
1. Eager vs lazy execution?
2. What are predicate pushdown and projection pushdown?
3. When would you still choose pandas?
4. In `shopflow`, when would you use SQL, and when a DataFrame?

<details><summary>Answers</summary>

1. Eager runs each step immediately. Lazy builds a plan first and then optimizes the whole query before running it.
2. Predicate pushdown filters rows while reading. Projection pushdown reads only the columns you need. Both mean less I/O and memory.
3. When you need its ecosystem (many libraries expect pandas), existing team code, or small data where speed doesn't matter.
4. SQL for set-based transformations inside the warehouse (marts), because it's portable and analysts can read it. DataFrames for complex Python logic, ML features or analysis. Both are valid. Consistency within a team matters most.
</details>

---

## Day 42 — 🛠 Data-quality checks

**Learn (10 min)**
- Common checks: **volume** (row count), **completeness** (nulls), **uniqueness** (keys), **validity** (accepted values or ranges), **freshness** (latest timestamp), **referential integrity** (foreign keys exist).
- Severity: `error` → fail the pipeline, `warn` → log and alert.
- Tools that do this at scale: dbt tests, Great Expectations, Soda.

**Do (40 min)** in `src/shopflow/quality.py`
1. `@dataclass class CheckResult: name, table, passed, severity, details`
2. Functions returning a `CheckResult`: `check_row_count(con, table, min_rows)`, `check_not_null(con, table, column)`, `check_unique(con, table, key)`, `check_foreign_key(con, child, fk, parent, pk)` (do all cart item product_ids exist in products?).
3. `run_checks(con, checks) -> list[CheckResult]`. Log each one, save the results to a `dq_results` table (with `run_date`), and raise `DataQualityError` if any check with severity `error` failed.
4. Tests: a passing dataset, plus one that fails each check.

**Check yourself**
1. Give one data-quality check for each layer: raw, staging, marts.
2. Why store check results in a table?
3. `warn` vs `error`: how do you decide?
4. What's referential integrity, and why might it break with API data?

<details><summary>Answers</summary>

1. Raw: the row count is above zero and close to the previous run. Staging: primary key unique, required fields not null. Marts: revenue isn't negative, and the totals match staging.
2. Trends over time (is the null rate growing?), dashboards and alerts, and evidence for audits.
3. `error` when the data would be wrong or misleading if published (duplicate keys, empty load). `warn` for suspicious but usable data (slightly fewer rows than usual).
4. Every foreign key points to an existing record. With APIs, entities are extracted at different moments or through different endpoints, so a cart can reference a product you haven't fetched (or one that was deleted).
</details>

---

## Day 43 — Week 7 review 🔁

**Do (30 min)**
1. Wire `run_checks` into `main()`: extract → validate → load → **check** → transform → **check marts**.
2. README: a "Data quality" section listing your checks and their severities.

**Weekly quiz**
1. pandas, polars or SQL: one sentence each on when to use it.
2. You merge two DataFrames and the row count goes from 1,000 to 1,350. What happened, and how would you prevent it?
3. What does `df[df.x > 1]["y"] = 0` do, and what should you write instead?
4. Name 6 categories of data-quality checks.
5. A check fails at 3 a.m. What should the pipeline do with the data, and what should it do about people?

<details><summary>Answers</summary>

1. (Yours.) pandas for ecosystem and small to medium data. polars for performance and bigger single-machine data. SQL for warehouse transformations.
2. The merge key isn't unique on the right side (fan-out). Use `validate=`, dedupe first, and check the counts.
3. It writes to a temporary copy, so the original doesn't change. Use `df.loc[df.x > 1, "y"] = 0`.
4. Volume, completeness, uniqueness, validity, freshness, referential integrity (also: consistency/reconciliation, schema).
5. Don't publish bad data downstream (stop before the marts, or keep yesterday's version). Alert the on-call person with a clear message and context.
</details>

📝 Confidence log.

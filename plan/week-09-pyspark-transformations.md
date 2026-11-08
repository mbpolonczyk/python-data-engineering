# Week 9 · PySpark transformations and testing

**Phase 4 — PySpark** · Days 49–53
[← Week 8](week-08-pyspark-fundamentals.md) · [Plan overview](README.md) · [Week 10 →](week-10-pyspark-performance-delta.md)

> **This week's outcome:** you can write the transformations real ETL jobs need (joins, windows, SQL) without the classic bugs, and you can prove they work with fast pytest tests.
>
> **Project milestone:** `shopflow/src/shopflow/spark/marts.py` builds daily revenue, customer stats and product performance in PySpark, with tests.

| Day | Topic | Time |
|---|---|---|
| 49 | Joins and their traps | ~50 min |
| 50 | Window functions | ~50 min |
| 51 | Spark SQL, UDFs and built-ins | ~45 min |
| 52 | Testing PySpark with pytest | ~50 min |
| 53 | 🛠 Build day: Spark marts + tests + quiz | ~60 min |

Use the shared sample data below on days 49–50. Put it in `src/day49/data.py` with a `make_data(spark)` function, so you can import it later.

```python
orders = spark.createDataFrame(
    [(1, 10, 101, 2, "2026-03-01"), (2, 11, 102, 1, "2026-03-01"),
     (3, 12, 999, 1, "2026-03-02"), (4, 10, None, 3, "2026-03-02")],
    "order_id INT, customer_id INT, product_id INT, quantity INT, updated_at STRING")
products = spark.createDataFrame(
    [(101, "Drill X200", "tools", "2026-02-01"), (102, "Saw S1", "tools", "2026-02-01"),
     (103, "Glove Pro", "safety", "2026-02-01")],
    "product_id INT, title STRING, category STRING, updated_at STRING")
supplier_prices = spark.createDataFrame(
    [(101, 80.0, "2026-01-01"), (101, 85.0, "2026-03-01"), (102, 30.0, "2026-01-01")],
    "product_id INT, cost DOUBLE, valid_from STRING")
```

---

<a id="day-49"></a>
## Day 49 · Joins and their traps

⏱ ~50 min · 📁 `src/day49/exercises49.py`

> 🎯 **By the end you can:** pick the right join type, and spot row explosions, lost null keys and ambiguous columns.
> 💼 **At work:** a duplicated key in a lookup table silently doubles revenue. This is the most common bug in ETL reviews.

### 📖 Learn (10 min)
- `a.join(b, on="product_id", how="left")`. Joining on a **column name** keeps one `product_id` column. Joining on an **expression** (`a.product_id == b.product_id`) keeps both.
- `how`: `inner`, `left`, `full`, `left_semi` (rows in `a` that have a match, only `a`'s columns), `left_anti` (rows in `a` with **no** match).
- If the right side has 2 rows for a key, each matching left row becomes 2 rows: a **fan-out**.
- `null` never equals `null`, so rows with null keys never match. `a.k.eqNullSafe(b.k)` treats two nulls as equal.
- Same column name on both sides? Use `a.alias("o")`, `b.alias("p")`, then `F.col("o.updated_at")`.
- Docs: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.join.html

### 💻 Do (35 min)
- [ ] **1.** **Predict, then check** the row counts: `orders` inner `products`, `orders` left `products`, `orders` left_anti `products`, `products` left_semi `orders`.
- [ ] **2.** Use the left_anti join to find orders with an unknown or missing product. Where should these rows go in shopflow? (Think Week 5.)
- [ ] **3.** *Bug hunt:* join `orders` and `products` on `orders.product_id == products.product_id`, then `.select("order_id", "updated_at")`. Read the error. Fix it with aliases, and rename to `order_updated_at` / `product_updated_at`.
- [ ] **4.** Join `orders` to `supplier_prices` on `product_id`. How many rows came back for order 1? Write a reusable guard `assert_no_fanout(before: DataFrame, after: DataFrame)` that raises if the row count grew.
- [ ] **5.** Build `order_lines`: orders + product title/category + cost, using left joins, with the guard after each join. For now, keep only the **latest** supplier price per product (`groupBy` + `max("valid_from")`, then join back).
- ⭐ *Stretch:* a "point-in-time" join: use the cost that was valid **on the order date** (`valid_from <= order_date`). You'll finish it with a window tomorrow.

### ✅ Check yourself (5 min)
1. When is `left_semi` better than an inner join followed by `select` on the left columns?
2. Order 4 has `product_id = null`. Does it appear in the inner join? In the left join?
3. Why does `on="product_id"` avoid the ambiguous column problem, but `on=a.product_id == b.product_id` doesn't?
4. A left join from orders to a lookup table returns more rows than `orders` has. What does that tell you, and what do you do?

<details><summary>Answers</summary>

1. When you only want to **filter** the left side. A semi join never duplicates left rows, even if the right side has many matches, and it doesn't add columns.
2. Not in the inner join. In the left join, yes, with nulls in the product columns. A null key never matches anything.
3. With a column name, Spark merges the key into one column. With an expression, both `product_id` columns stay, so a bare `"product_id"` is ambiguous.
4. The lookup table has duplicate keys. Find them (`groupBy(key).count().filter("count > 1")`), then fix the grain at the source or pick one row per key. Never "fix" it with `distinct()` after the join.
</details>

---

<a id="day-50"></a>
## Day 50 · Window functions

⏱ ~50 min · 📁 `src/day50/exercises50.py`

> 🎯 **By the end you can:** dedupe to the latest version of each record, and compute running totals, day-over-day changes and rankings.
> 💼 **At work:** "keep the latest row per key" is the dedupe step in every incremental staging table.

### 📖 Learn (10 min)
- `from pyspark.sql import Window`. Define `w = Window.partitionBy("order_id").orderBy(F.col("updated_at").desc())`, then `F.row_number().over(w)`.
- Same as the SQL windows from Week 6: `row_number`, `rank`, `dense_rank`, `lag`, `lead`, `sum().over(w)`.
- With `orderBy` and no frame, the default frame is **RANGE from the start to the current row**: rows that tie on the order column are summed together. Use `.rowsBetween(Window.unboundedPreceding, Window.currentRow)` for a strict running total.
- `rowsBetween` counts rows. `rangeBetween` uses the **values** of the order column (e.g. "the last 3 days"), so missing days are handled correctly.
- A window without `partitionBy` moves all data to **one partition**. Fine for a small daily table, a disaster for a big one.

### 💻 Do (35 min)
- [ ] **1.** Dedupe these ERP order versions to the latest per `order_id`. Expected: 3 rows (1 paid, 2 cancelled, 3 paid).
  ```python
  versions = spark.createDataFrame(
      [(1, "pending", 120.0, "2026-03-01 10:00:00"), (1, "paid", 120.0, "2026-03-01 12:00:00"),
       (2, "pending", 80.0, "2026-03-01 11:00:00"), (2, "cancelled", 80.0, "2026-03-02 09:00:00"),
       (3, "paid", 45.0, "2026-03-02 10:00:00")],
      "order_id INT, status STRING, amount DOUBLE, updated_at STRING",
  ).withColumn("updated_at", F.to_timestamp("updated_at"))
  ```
  Write it as a reusable function `latest_by_key(df, key_cols, order_col)`.
- [ ] **2.** *Explain why:* add a 6th row that ties with another row of order 1 on `updated_at`. Run your dedupe a few times (try different `repartition` numbers). Is the result stable? Add a tie-breaker column to the `orderBy`.
- [ ] **3.** Daily revenue `(2026-03-01, 200.0), (2026-03-02, 125.0), (2026-03-04, 90.0), (2026-03-05, 310.0)` (convert `day` with `F.to_date`): add `running_total`, `prev_day_revenue` (`lag`) and `change`. Expected running totals: 200, 325, 415, 725.
- [ ] **4.** Add a 3-day rolling sum two ways: `rowsBetween(-2, 0)` and `rangeBetween(-2 * 86400, 0)` ordered by `F.unix_timestamp("day")`. They differ on 2026-03-04 (415 vs 215). Which is correct, and why?
- [ ] **5.** Customer spend `A=300, B=300, C=150`: add `row_number`, `rank` and `dense_rank` ordered by spend descending. Predict the values first.
- ⭐ *Stretch:* finish yesterday's point-in-time join: join orders to all supplier prices with `valid_from <= order_date`, then keep the latest `valid_from` per order with `latest_by_key`.

### ✅ Check yourself (5 min)
1. Why `row_number` and not `rank` for deduping?
2. What does `lag("revenue", 1)` return for the first row of a partition?
3. Why is `F.sum("x").over(Window.orderBy("day"))` risky on a big table?
4. Someone dedupes with `groupBy("order_id").agg(F.max("updated_at"))`. What's missing?

<details><summary>Answers</summary>

1. `rank` gives tied rows the same number, so `rank == 1` can keep two rows. `row_number` always gives exactly one row number 1.
2. `null`, unless you pass a default: `F.lag("revenue", 1, 0)`.
3. There's no `partitionBy`, so Spark moves every row to one partition and one task does all the work.
4. You only get the key and the max timestamp, not the rest of the row. You'd have to join back (and handle ties). `row_number` keeps the whole latest row in one step.
</details>

---

<a id="day-51"></a>
## Day 51 · Spark SQL, UDFs and built-ins

⏱ ~45 min · 📁 `src/day51/exercises51.py`

> 🎯 **By the end you can:** mix SQL and the DataFrame API, and replace slow Python UDFs with built-in functions.
> 💼 **At work:** teams mix SQL and Python freely. Knowing why UDFs are slow is a classic senior interview question.

### 📖 Learn (10 min)
- `df.createOrReplaceTempView("orders")`, then `spark.sql("SELECT ... FROM orders")` returns a normal DataFrame. Both APIs produce the **same plan**; pick whichever reads better.
- A Python `@F.udf` runs row by row in a separate Python process. Every row is **serialized** from the JVM to Python and back, and the optimizer can't see inside it.
- `@F.pandas_udf` uses Apache Arrow to send **batches** as pandas Series. It's much faster than a plain UDF, but slower than a built-in. Needs `uv add pyarrow`.
- Rule: built-in function > SQL expression (`F.expr`) > `pandas_udf` > plain `udf`.
- Benchmark without collecting: `df.write.format("noop").mode("overwrite").save()` runs the full job and throws the result away.
- Docs: https://spark.apache.org/docs/latest/api/python/user_guide/udfandudtf.html

### 💻 Do (30 min)
- [ ] **1.** Register your Day 49 `orders` and `products` as views. Port one Week 6 DuckDB query **unchanged** into `spark.sql(...)`. Did it run? Note any syntax you had to change.
- [ ] **2.** Mix them: start with `spark.sql(...)`, then continue with `.filter(...)` and `.withColumn(...)`. Compare `explain()` with a pure DataFrame version.
- [ ] **3.** Time these UDFs on `spark.range(3_000_000).withColumn("price", (F.col("id") % 500).cast("double")).withColumn("name", F.lit("  anna smith "))`:
  ```python
  @F.udf("string")
  def price_band(price):
      if price is None: return "unknown"
      if price < 50: return "cheap"
      return "mid" if price < 200 else "premium"

  @F.udf("string")
  def clean_name(s):
      return s.strip().title() if s is not None else None
  ```
- [ ] **4.** Rewrite both with built-ins (`F.when`, `F.initcap`, `F.trim`) and time again. Then compare results with `exceptAll`. Do `initcap` and `str.title` ever differ? Try `"o'neil"`.
- [ ] **5.** Write `price_band` as a `pandas_udf` (type hints `pd.Series -> pd.Series`, use `numpy.select` or `pd.cut`) and time it too. Rank the three versions.
- ⭐ *Stretch:* look at `explain()` for the UDF version. Find `BatchEvalPython` (or `ArrowEvalPython`) in the plan.

### ✅ Check yourself (5 min)
1. Is `spark.sql("...")` slower than the DataFrame API?
2. Why is a Python UDF slow?
3. When is a `pandas_udf` still the right choice?
4. A UDF filter on `country` stops Spark from pushing the filter into the Parquet scan. Why?

<details><summary>Answers</summary>

1. No. Both go through the same optimizer (Catalyst) and produce the same physical plan.
2. Each row is serialized between the JVM and a Python worker and back, processed one at a time, and the optimizer treats the UDF as a black box.
3. When no built-in can do it: calling a Python library (a parser, a statistics function, a model), with vectorized pandas or numpy code inside.
4. Spark can't translate Python code into a file-level filter, so it has to read every row and send it to Python first.
</details>

---

<a id="day-52"></a>
## Day 52 · Testing PySpark with pytest

⏱ ~50 min · 📁 `shopflow/tests/conftest.py`, `shopflow/tests/spark/`

> 🎯 **By the end you can:** test Spark transformations with tiny inline DataFrames, quickly and reliably.
> 💼 **At work:** untested Spark jobs are the norm, so tested ones stand out in code review and in interviews.

### 📖 Learn (10 min)
- Structure each job as **pure functions** `DataFrame -> DataFrame`, with reading and writing at the edges. It's the Week 1 rule (Day 12) again: pure logic is easy to test.
- Starting Spark takes seconds, so create **one session per test run**: a `scope="session"` fixture with `local[1]` and `spark.sql.shuffle.partitions=1`.
- `from pyspark.testing import assertDataFrameEqual, assertSchemaEqual` (Spark 3.5+). Row order is ignored by default (`checkRowOrder=False`), floats are compared with a tolerance (`rtol`), and you get a readable diff.
- `chispa` (`assert_df_equality(a, b, ignore_row_order=True)`) is a popular alternative, often seen in older codebases.
- Docs: https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html

### 💻 Do (35 min)
- [ ] **1.** `tests/conftest.py`:
  ```python
  import pytest
  from pyspark.sql import SparkSession

  @pytest.fixture(scope="session")
  def spark():
      spark = (SparkSession.builder.master("local[1]").appName("shopflow-tests")
               .config("spark.sql.shuffle.partitions", "1")
               .config("spark.ui.enabled", "false")
               .config("spark.sql.session.timeZone", "UTC")
               .getOrCreate())
      yield spark
      spark.stop()
  ```
- [ ] **2.** Refactor `spark/staging.py` from Day 48: split each entity into `read_…(spark, path)`, `transform_…(df) -> DataFrame` and `write_…(df, path)`. Move `latest_by_key` (Day 50) into `spark/utils.py` and use it instead of `dropDuplicates`.
- [ ] **3.** `tests/spark/test_utils.py`: test `latest_by_key` with the Day 50 versions data. Build `expected` with `spark.createDataFrame(...)` and compare with `assertDataFrameEqual`.
- [ ] **4.** Add edge-case tests: an empty input DataFrame (same schema, zero rows), a null key, and a tie on `updated_at`. Also test that dedupe is **idempotent**: `latest_by_key(latest_by_key(df))` equals `latest_by_key(df)`.
- [ ] **5.** *Break it on purpose:* change the expected amount to `120.01` and read the diff. Then make a column nullable in one schema only. Does `assertDataFrameEqual` care? Check `assertSchemaEqual`.
- [ ] **6.** Run `uv run pytest tests/spark -q --durations=5`. Fill in **playbook §6** with your Spark testing pattern.
- ⭐ *Stretch:* rewrite one test with chispa and compare the error messages.

### ✅ Check yourself (5 min)
1. Why `scope="session"` for the Spark fixture?
2. Why set shuffle partitions to 1 in tests?
3. Why test `transform_orders(df)` and not the whole `run()` that reads files?
4. Your test passes locally but fails in CI with a one-hour difference in timestamps. What's the likely cause?

<details><summary>Answers</summary>

1. Starting a SparkSession takes several seconds. One session shared by all tests keeps the suite fast.
2. The default of 200 creates 200 tiny tasks for every shuffle on a few rows, which makes tests much slower for no benefit.
3. Pure functions need no files, mocks or cleanup, and each test controls its input exactly. Keep one small end-to-end test for the read/write wiring.
4. The session time zone isn't fixed, so it follows the machine's. Set `spark.sql.session.timeZone=UTC` in the fixture and in the job.
</details>

---

<a id="day-53"></a>
## Day 53 · 🛠 Build day: Spark marts + tests + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/spark/marts.py`

> 🎯 **By the end you can:** build tested marts in PySpark that match your DuckDB marts.
> 💼 **At work:** this is a typical PySpark ticket: business logic, joins, windows and tests.

### 💻 Do (45 min)
- [ ] **1.** In `marts.py`, write pure functions over your staging DataFrames (adapt the column names to your Week 4 ERP schema):
  - `mart_daily_revenue(orders)`: `order_date`, `orders`, `customers`, `revenue`. Exclude cancelled orders.
  - `mart_customer_stats(orders)`: `customer_id`, `orders`, `total_spend`, `avg_order_value`, `first_order_date`, `last_order_date`, `spend_rank` (`dense_rank`).
  - `mart_product_performance(orders, products, supplier_prices)`: `product_id`, `title`, `units`, `revenue`, `cost`, `margin`, `margin_pct`. Use the point-in-time cost from Day 50 and `assert_no_fanout` from Day 49.
- [ ] **2.** `tests/spark/test_marts.py`: one test per mart with 4–6 hand-made rows and numbers **you calculated by hand**. Include a cancelled order and a product without a supplier price.
- [ ] **3.** `run(spark, staging_path, marts_path)` reads staging, builds the marts and writes Parquet to `data/marts/<mart>/`. Add a `__main__` block and run it.
- [ ] **4.** Compare each mart with the DuckDB version from Week 6 using `exceptAll` both ways. Explain any difference in a comment.
- [ ] **5.** Fill in **playbook §5**: which dedupe key and which row you keep, and how you protect joins from fan-out.

### ✅ Weekly quiz
1. *Explain out loud, as in an interview:* how do you dedupe a table to the latest version of each record in Spark, and what can go wrong?
2. A left join returns more rows than the left table has. Why?
3. `left_semi` vs `left_anti`: give one shopflow use for each.
4. Why avoid Python UDFs, and what do you use instead?
5. How do you structure a PySpark job so it's testable?

<details><summary>Answers</summary>

1. A window partitioned by the business key, ordered by `updated_at` descending (plus a tie-breaker), with `row_number`, then keep `rn == 1`. Risks: ties without a tie-breaker give random results, and null keys all fall into one group.
2. The right side has duplicate keys, so matching rows fan out.
3. `left_semi`: keep only products that were ordered. `left_anti`: find orders whose product doesn't exist, and quarantine them.
4. They serialize every row between the JVM and Python and block optimizations. Use built-in functions, `F.expr`/SQL, or a `pandas_udf` if you really need Python.
5. Pure `DataFrame -> DataFrame` functions for the logic, I/O at the edges, a session-scoped SparkSession fixture, and tiny inline inputs with hand-calculated expected outputs.
</details>

---

## 🏁 End of week 9: I can…
- [ ] Choose a join type and guard against fan-out, null keys and ambiguous columns
- [ ] Dedupe with `row_number` and use running totals, `lag` and ranking
- [ ] Replace a Python UDF with built-ins and explain why it's faster
- [ ] Test PySpark transformations with pytest and `assertDataFrameEqual`

📈 Rate your confidence for Week 9 in the [progress tracker](README.md#-progress-tracker).

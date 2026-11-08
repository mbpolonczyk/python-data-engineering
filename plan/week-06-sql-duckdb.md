# Week 6 · SQL transformations and loading with DuckDB

**Phase 3 — ETL transformations** · Days 34–38
[← Week 5](week-05-validation.md) · [Plan overview](README.md) · [Week 7 →](week-07-dataframes-quality.md)

> **This week's outcome:** you transform validated data into clean staging tables and business-ready marts with SQL, and your loads are safe to rerun.
>
> **Project milestone:** `shopflow transform` runs the SQL layers in order (staging → marts) in a DuckDB warehouse, joining API products, ERP orders and supplier prices, and exports the marts to Parquet.

**DuckDB** is an analytical database that runs inside your Python process: no server, no setup. The SQL and the patterns transfer directly to Snowflake, BigQuery, Databricks and Spark SQL.

| Day | Topic | Time |
|---|---|---|
| 34 | DuckDB from Python: query files, write Parquet | ~45 min |
| 35 | Idempotent loads: delete+insert and upserts | ~50 min |
| 36 | SQL for transformations: CTEs and window functions | ~50 min |
| 37 | Layered modelling: raw → staging → marts, SCD type 2 | ~55 min |
| 38 | 🛠 Build day: the transform module + quiz | ~60 min |

---

<a id="day-34"></a>
## Day 34 · DuckDB from Python: query files, write Parquet

⏱ ~45 min · 📁 `src/day34/exercises34.py`

> 🎯 **By the end you can:** query JSON, CSV and Parquet files with SQL straight from Python, and move data between DuckDB and pandas.
> 💼 **At work:** "just query the files" is the fastest way to explore a new source before you build anything.

### 📖 Learn (10 min)
- **OLAP** (column store, big scans and aggregations) vs **OLTP** (row store, many small writes, like your SQLite ERP).
- `con = duckdb.connect("data/warehouse.duckdb")` (a file) or `duckdb.connect()` (in memory).
- `con.sql(query)` returns a **relation**: a query you can keep building on. Get results with `.fetchall()`, `.df()` (pandas), `.pl()` (polars) or `.show()`.
- `con.execute(query, [params])` for statements with values. **Always `?` parameters, never f-strings.**
- Files are tables: `read_json_auto('…/*.jsonl')`, `read_csv('…')`, `read_parquet('…')`. `hive_partitioning = true` turns `load_date=2026-03-01/` folders into a column.
- `COPY (query) TO 'x.parquet' (FORMAT parquet)` writes Parquet: columnar, compressed, typed.
- `con.sql("SELECT * FROM df")` can read a pandas DataFrame named `df` directly.
- Docs: https://duckdb.org/docs/stable/clients/python/overview

### 💻 Do (30 min)
- [ ] **1.** In `shopflow/`: `uv add duckdb pandas`. Run today's file with that environment: `uv run --project shopflow python src/day34/exercises34.py`.
- [ ] **2.** Query your validated products from Week 5 without loading them first:
  ```sql
  SELECT load_date, category, count(*) AS n, round(avg(price), 2) AS avg_price
  FROM read_json_auto('data/validated/dummyjson/products/*/*.jsonl', hive_partitioning = true)
  GROUP BY ALL ORDER BY n DESC
  ```
  Then run `DESCRIBE` on the same `SELECT *`. Which types did DuckDB infer?
- [ ] **3.** Write the products to `data/practice/products.parquet` with `COPY`. Compare its size with the JSONL files (`Get-ChildItem data/validated/dummyjson/products -Recurse | Measure-Object Length -Sum`).
- [ ] **4.** Round trip: `.df()` the ERP orders, add a column `amount_eur = amount * 1.0` in pandas, then aggregate that DataFrame with `con.sql("SELECT ... FROM orders_df")`.
- [ ] **5.** *Bug hunt:* write `orders_for(status)` with an f-string and call it with `"x' OR '1'='1"`. What comes back? Fix it with `con.execute(sql, [status])`.
- ⭐ *Stretch:* `EXPLAIN` a query on the Parquet file that selects 2 columns. Find the projection in the plan.

### ✅ Check yourself (5 min)
1. Why is a column store faster for `SUM(amount) GROUP BY day`?
2. What does `hive_partitioning = true` give you?
3. `con.sql(...)` vs `con.execute(..., params)`: when do you use which?
4. When would you pick DuckDB, Postgres, or Spark?

<details><summary>Answers</summary>

1. It reads only the 2 columns it needs, and similar values stored together compress well. A row store reads every column of every row.
2. A column built from the folder names (here `load_date`), so you can filter and group by partition, and DuckDB can skip whole folders.
3. `con.sql` for building queries and getting relations (no parameters). `con.execute` when the query contains values, so you can pass them safely as parameters.
4. DuckDB: single-machine analytics, local pipelines and tests, up to roughly hundreds of GB. Postgres: application data with many small transactions. Spark: data or workloads too big for one machine.
</details>

---

<a id="day-35"></a>
## Day 35 · Idempotent loads: delete+insert and upserts

⏱ ~50 min · 📁 `src/day35/exercises35.py`

> 🎯 **By the end you can:** load data so that rerunning the same job gives exactly the same table.
> 💼 **At work:** jobs get retried and backfilled all the time. A load that appends twice doubles yesterday's revenue.

### 📖 Learn (15 min)
- **Idempotent:** running it once or five times gives the same result.
- **Delete+insert by partition:** `DELETE FROM t WHERE load_date = ?` then `INSERT`, **in one transaction** (`con.begin()`, `con.commit()`, `con.rollback()`). Use it when you reprocess whole days.
- **Upsert** needs a `PRIMARY KEY` or `UNIQUE` column. `INSERT OR REPLACE INTO t ...` overwrites every column. `INSERT INTO t ... ON CONFLICT (id) DO UPDATE SET col = EXCLUDED.col WHERE ...` gives you control. Use it when single records change over time.
- DuckDB 1.4+ also has `MERGE INTO` (check the docs for your version). Spark and Delta Lake use `MERGE` too (Week 10).
- Gotcha: if one batch has the **same key twice**, DuckDB applies only one update, and not necessarily the last one (older versions raise an error). Dedupe the batch first (tomorrow's `ROW_NUMBER`).
- Docs: https://duckdb.org/docs/stable/sql/statements/insert

### 💻 Do (30 min)
- [ ] **1.** *See the problem:* create `stg_orders(order_id INTEGER, status VARCHAR, amount DOUBLE, updated_at TIMESTAMP)` with no key. Insert batch 1 twice with `executemany`. Count the rows.
  ```python
  batch1 = [(1, "paid", 120.0, "2026-03-01 10:30"), (2, "paid", 80.0, "2026-03-01 11:00"),
            (3, "paid", 45.5, "2026-03-02 08:15")]
  batch2 = [(2, "shipped", 80.0, "2026-03-03 10:00"), (4, "paid", 200.0, "2026-03-03 14:00"),
            (1, "pending", 120.0, "2026-03-01 09:00")]   # order 1 arrives late, and it's OLDER
  ```
- [ ] **2.** Delete+insert: add a `load_date DATE` column and write `load_partition(con, rows, load_date)` that deletes and inserts inside a transaction. Run it twice for the same date and assert the count doesn't change.
- [ ] **3.** *Explain why:* raise an exception between the `DELETE` and the `INSERT`. What's in the table with the transaction, and what would be there without it?
- [ ] **4.** Upsert: recreate the table with `order_id INTEGER PRIMARY KEY`. Load batch 1, then batch 2 with `INSERT OR REPLACE`. *Predict:* what's order 1's status now? Is that right?
- [ ] **5.** Fix it so stale records can't overwrite newer ones:
  ```sql
  INSERT INTO stg_orders VALUES (?, ?, ?, ?)
  ON CONFLICT (order_id) DO UPDATE
  SET status = EXCLUDED.status, amount = EXCLUDED.amount, updated_at = EXCLUDED.updated_at
  WHERE EXCLUDED.updated_at > updated_at   -- unqualified = the existing row
  ```
  Expected after both batches: 4 rows, order 1 `paid`, order 2 `shipped`.
- [ ] **6.** 📘 Playbook §5: write down which pattern you'd pick for each `shopflow` source, and why.

### ✅ Check yourself (5 min)
1. Delete+insert vs upsert: when do you use each?
2. Why must the delete and the insert be in one transaction?
3. Why did `INSERT OR REPLACE` give the wrong answer in task 4?
4. A full rebuild (`CREATE OR REPLACE TABLE`) is also idempotent. Why not always do that?

<details><summary>Answers</summary>

1. Delete+insert when the unit of work is a whole partition (a day of clickstream files). Upsert when individual records change and you have a reliable key (ERP orders with `updated_at`).
2. Otherwise a crash between them leaves the partition empty, and the dashboard shows zero sales for that day.
3. It always takes the incoming row. A late-arriving older version overwrote the newer `paid` status. Comparing `updated_at` keeps the latest version, whatever order the records arrive in.
4. It's simple and always correct, but it reprocesses everything on every run. That's fine for small tables and too slow or expensive for big ones.
</details>

---

<a id="day-36"></a>
## Day 36 · SQL for transformations: CTEs and window functions

⏱ ~50 min · 📁 `src/day36/exercises36.py` (SQL in strings or `src/day36/*.sql`)

> 🎯 **By the end you can:** dedupe to the latest version of each record, and compute running totals and day-over-day changes.
> 💼 **At work:** "keep the latest row per key" is the most common staging step there is, and a favourite interview question.

### 📖 Learn (10 min)
- **CTE:** `WITH step1 AS (...), step2 AS (SELECT ... FROM step1) SELECT ...` reads top to bottom, like a pipeline.
- **Window function:** `f() OVER (PARTITION BY key ORDER BY col)` computes per group **without** collapsing rows.
- `ROW_NUMBER()` 1,2,3 · `RANK()` 1,1,3 · `DENSE_RANK()` 1,1,2 · `LAG(col)` previous row · `SUM(col) OVER (ORDER BY day)` running total.
- DuckDB's `QUALIFY` filters on a window result: `QUALIFY ROW_NUMBER() OVER (...) = 1`.
- Docs: https://duckdb.org/docs/stable/sql/functions/window_functions

### 💻 Do (35 min)
Use this as a CTE at the top of each query:
```sql
WITH orders(order_id, customer_id, status, amount, updated_at) AS (VALUES
  (1, 7, 'pending',   120.0, TIMESTAMP '2026-03-01 09:00'),
  (1, 7, 'paid',      120.0, TIMESTAMP '2026-03-01 10:30'),
  (2, 8, 'paid',       80.0, TIMESTAMP '2026-03-01 11:00'),
  (3, 7, 'paid',       45.5, TIMESTAMP '2026-03-02 08:15'),
  (3, 7, 'cancelled',  45.5, TIMESTAMP '2026-03-02 09:00'),
  (4, 9, 'paid',      200.0, TIMESTAMP '2026-03-03 14:00'),
  (5, 8, 'paid',       95.0, TIMESTAMP '2026-03-03 16:45'))
```
- [ ] **1.** Dedupe: keep the latest row per `order_id` by `updated_at`. Write it twice: with a subquery and `WHERE rn = 1`, then with `QUALIFY`. Expected: 5 rows, order 3 `cancelled`.
- [ ] **2.** *Bug hunt:* a colleague filters `WHERE status = 'paid'` **before** deduping. What's wrong with order 3 in their result?
- [ ] **3.** Daily revenue of paid orders (after dedupe), with a running total and the change from the previous day using `LAG`. Expected days: 03-01 → 200.0, 03-03 → 295.0. Why is 03-02 missing, and how could a calendar table fix it?
- [ ] **4.** Rank customers by paid spend with `RANK` and `DENSE_RANK`. Expected order: 9 (200), 8 (175), 7 (120).
- [ ] **5.** *Interview style:* for each customer, show each order with the previous order's amount and the time since it (`LAG` with `PARTITION BY customer_id`).
- ⭐ *Stretch:* two rows with the **same** `updated_at` for one key: which one does `ROW_NUMBER` keep? Make it deterministic.

### ✅ Check yourself (5 min)
1. `WHERE` vs `HAVING` vs `QUALIFY`?
2. What do `ROW_NUMBER`, `RANK` and `DENSE_RANK` return for 100, 100, 90?
3. Why does `GROUP BY` lose rows but a window function doesn't?
4. `LEFT JOIN b ON ... WHERE b.x = 1` vs `LEFT JOIN b ON ... AND b.x = 1`?

<details><summary>Answers</summary>

1. `WHERE` filters rows before grouping, `HAVING` filters groups after aggregation, `QUALIFY` filters after window functions.
2. ROW_NUMBER 1,2,3 · RANK 1,1,3 · DENSE_RANK 1,1,2.
3. `GROUP BY` collapses each group into one row. A window computes a value per group and attaches it to every row.
4. The `WHERE` version drops rows where `b` is NULL, which silently turns it into an inner join. The `ON` version keeps every row from `a`.
</details>

---

<a id="day-37"></a>
## Day 37 · Layered modelling: raw → staging → marts, SCD type 2

⏱ ~55 min · 📁 `shopflow/src/shopflow/transform/sql/`

> 🎯 **By the end you can:** split transformations into clear layers, join several sources at the right grain, and explain SCD type 2.
> 💼 **At work:** this is how dbt projects and warehouses are organized. Interviewers will ask "how would you model this?"

### 📖 Learn (15 min)
- **Raw:** files as received. **Staging:** one table per source entity, typed, renamed to snake_case, deduped (`stg_erp__orders`). **Marts:** business-shaped, joined and aggregated (`mart_daily_revenue`).
- **Grain:** what one row means. Decide it before writing a join. Joining to a table that has several rows per key **multiplies** your rows (fan-out).
- **SCD type 1** overwrites a changed attribute (no history). **SCD type 2** keeps history: one row per version with `valid_from`, `valid_to` and `is_current`.
- Docs: https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview (dbt's guide, the same ideas)

### 💻 Do (35 min)
- [ ] **1.** SCD2 warm-up (in `src/day37/scd2.py`): turn price changes into versions with `LEAD(changed_at) OVER (PARTITION BY product_id ORDER BY changed_at) AS valid_to`, plus `is_current`:
  ```sql
  WITH price_changes(product_id, cost_price, changed_at) AS (VALUES
    (101, 10.00, DATE '2026-01-01'), (101, 12.00, DATE '2026-03-01'), (102, 4.00, DATE '2026-01-15'))
  ```
  Join orders of product 101 on `2026-02-10` and `2026-03-05` to the right version (`order_date >= valid_from AND (order_date < valid_to OR valid_to IS NULL)`). Expected costs: 10.00 and 12.00.
- [ ] **2.** In `transform/sql/staging/`, write one file per entity, each a `CREATE OR REPLACE TABLE ... AS`: `stg_dummyjson__products`, `stg_erp__orders` (latest per key, Day 36), `stg_supplier__prices` (SCD2 versions, task 1). Read from views like `src_erp__orders` over `data/validated/` (you'll create them from Python on Day 38). Adapt column names to your Week 4 schema.
- [ ] **3.** In `transform/sql/marts/`: `mart_daily_revenue` (date, orders, revenue, cost, margin), `mart_customer_stats` (customer, orders, total spend, first/last order date) and `mart_product_performance` (product, category from the API, units, revenue, margin from supplier costs).
- [ ] **4.** *Explain why:* if you joined orders to **all** supplier price rows by `product_id` only, what would happen to revenue? Check by counting rows before and after the join.
- [ ] **5.** 📘 Playbook §5: your staging rules (dedupe key, which row wins, how late records are handled).

### ✅ Check yourself (5 min)
1. Why keep staging 1:1 with the source instead of joining straight from raw?
2. What's the grain of each of your three marts?
3. SCD1 vs SCD2: which one for a customer's email, and which for a supplier's cost price?
4. Revenue in a mart doubled after you added a join. What's your first suspicion?

<details><summary>Answers</summary>

1. Cleaning happens once, in one place. Every mart reuses the same typed, deduped data. When a source changes, you fix one staging model.
2. One row per date; one row per customer; one row per product.
3. Email: usually SCD1 (you only need the current one). Cost price: SCD2, because margins for past orders must use the price that was valid **at the time**.
4. Fan-out: the joined table has more than one row per key (several price versions, duplicates). Check uniqueness of the join key and join on the correct grain.
</details>

---

<a id="day-38"></a>
## Day 38 · 🛠 Build day: the transform module + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/transform/run.py`, `shopflow/tests/test_transform.py`

> 🎯 **By the end you can:** run staging and marts in order with one command, and prove the numbers are right with tests.
> 💼 **At work:** this is a mini dbt. Knowing how it works inside makes real tools easy to learn.

### 💻 Do (45 min)
- [ ] **1.** `create_source_views(con, validated_dir)`: one `CREATE OR REPLACE VIEW src_<source>__<entity> AS SELECT * FROM read_json_auto('<path>/*/*.jsonl', hive_partitioning = true)` per entry in your Week 5 `CONTRACTS` registry. (The path comes from your config, not from users, so building it in Python is fine here.)
- [ ] **2.** `run_layer(con, layer)`: run every `.sql` file in `sql/<layer>/` in sorted order. Log the file name, the time taken and the row count of the table it created. Then `run_transform(db_path)`: views → staging → marts.
- [ ] **3.** Export each mart to `data/marts/<name>.parquet` with `COPY`. Add a `transform` command to your CLI.
- [ ] **4.** Tests: put tiny JSONL fixtures in `tests/fixtures/validated/` (3 products, 5 orders including one duplicate and one cancelled, 2 price versions). Run the whole transform on an in-memory database and assert the margin you calculated **by hand**.
- [ ] **5.** Run the transform twice and assert every mart has the same row count and totals. Commit.
- [ ] **6.** 📘 Finish Playbook §5 (for now. You'll add Spark and Delta notes in Weeks 8–10).

### ✅ Weekly quiz
1. Explain idempotency in your load and transform steps in two sentences.
2. A dashboard shows doubled revenue for yesterday. Name two likely causes in a pipeline like yours.
3. Write from memory: keep the latest row per `order_id` by `updated_at`.
4. *Explain out loud:* why do you have a staging layer between raw and marts?
5. Why does a late-arriving older record need special handling in an upsert?

<details><summary>Answers</summary>

1. (Yours.) For example: staging and marts are rebuilt with `CREATE OR REPLACE`, and incremental loads replace a whole partition or upsert by key in a transaction, so a rerun replaces instead of appending.
2. A load that appended instead of replacing (rerun or retry), or a join that fans out because the right side isn't unique on the join key.
3. `SELECT * FROM orders QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) = 1`
4. (Yours.) Raw keeps the source exactly as received, for audit and replay. Staging cleans each source once: types, names, dedupe. Marts then join clean inputs, so business logic isn't mixed with cleaning, and a source change is fixed in one place.
5. A plain overwrite would replace the newer version with the older one. Compare `updated_at` (or a version number) and only update when the incoming record is newer.
</details>

---

## 🏁 End of week 6: I can…
- [ ] Query JSON, CSV and Parquet files with DuckDB from Python
- [ ] Load data idempotently with delete+insert or an upsert, and explain the choice
- [ ] Dedupe with `ROW_NUMBER`, and use `LAG` and running totals
- [ ] Model raw → staging → marts, avoid fan-out, and explain SCD type 2

📈 Rate your confidence for Week 6 in the [progress tracker](README.md#-progress-tracker).

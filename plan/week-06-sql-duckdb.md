# Week 6 — SQL and loading with DuckDB

**DuckDB** is an analytical database that runs inside your Python process: no server, no setup. It's perfect for learning warehouse patterns that transfer directly to Snowflake, BigQuery and Databricks.

---

## Day 34 — DuckDB from Python 🧠

**Learn (15 min)**
- **OLTP** (row stores, many small transactions, e.g. Postgres for an app) vs **OLAP** (column stores, big scans and aggregations, e.g. warehouses and DuckDB).
- `con = duckdb.connect("data/warehouse.duckdb")`, `con.execute(sql, [params])`, `.fetchall()`, `.df()`, `.pl()`
- **Always use parameters (`?`), never f-strings,** for values in SQL.
- DuckDB can query files directly: `SELECT * FROM read_json_auto('data/staging/products/*/*.json')`
- Docs: https://duckdb.org/docs/api/python/overview

**Do (30 min)** in `shopflow` (or in `src/day34/` first if you prefer)
1. `uv add duckdb`
2. Create a table `t_orders(order_id INT, customer VARCHAR, value DOUBLE)`, insert the Day 7 orders with `executemany`, and query the totals per customer with `GROUP BY`.
3. Query your staging JSON files directly with `read_json_auto`.
4. **SQL injection demo:** write `find_by_customer(name)` with an f-string and call it with `"x' OR '1'='1"`. Then fix it with `?` parameters.

**Check yourself**
1. OLTP vs OLAP, and row store vs column store?
2. Why parameterized queries?
3. What does "in-process database" mean?
4. When would you pick DuckDB, Postgres or Spark/Snowflake?

<details><summary>Answers</summary>

1. OLTP handles many small reads and writes of whole rows (apps), so it stores rows together. OLAP scans a few columns over millions of rows (analytics), so it stores columns together, which compresses well and only reads the columns it needs.
2. They prevent SQL injection, handle quoting and types correctly, and let the database reuse query plans.
3. It runs as a library inside your program. There's no separate server process.
4. DuckDB: local or single-machine analytics, tests, data up to roughly hundreds of GB. Postgres: application data or OLTP. Spark/Snowflake/BigQuery: big data, many users, managed scale.
</details>

---

## Day 35 — 🛠 Loading staging tables idempotently

**Learn (15 min)**
- **Grain:** what one row of a table represents (one cart? one product within a cart?).
- Idempotent load patterns:
  - **Delete-insert by partition:** `DELETE WHERE _run_date = ?` then `INSERT` (inside one transaction).
  - **Upsert/MERGE:** `INSERT ... ON CONFLICT (id) DO UPDATE SET ...`
- **Transactions:** all or nothing.

**Do (35 min)**
1. `sql/ddl.sql`: `stg_products`, `stg_users`, `stg_carts` (one row per cart), `stg_cart_items` (one row per product within a cart: **flatten** the nested list). Add `_run_date DATE` and `_loaded_at TIMESTAMP` columns.
2. `load.py`: `load_entity(con, table, rows, run_date)` → `BEGIN; DELETE ... WHERE _run_date = ?; INSERT ...; COMMIT;` (roll back on error).
3. Run the load twice for the same date and assert the row counts don't change. Turn that into a **test** with an in-memory DB (`duckdb.connect(":memory:")`).

**Check yourself**
1. Delete-insert vs upsert/MERGE: when would you use each?
2. Why wrap the delete and insert in a transaction?
3. What's the grain of `stg_cart_items`?
4. Why flatten nested cart products into their own table?

<details><summary>Answers</summary>

1. Delete-insert when you reprocess whole partitions (a day of data). Upsert when individual records arrive or change over time and you have a reliable key.
2. Without it, a crash between the DELETE and the INSERT leaves the partition **empty**. A transaction makes it all or nothing.
3. One product line within one cart (cart_id + product_id).
4. Relational modelling: you can join, aggregate per product, and keep a clear grain. Nested arrays are awkward to query and aggregate.
</details>

---

## Day 36 — SQL for data engineering interviews 🧠

**Learn (10 min):** CTEs (`WITH`), window functions (`OVER (PARTITION BY … ORDER BY …)`), `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`, `SUM() OVER`, and DuckDB's `QUALIFY`.

**Do (40 min)**: write the queries in `sql/practice.sql` and run them from Python
1. Top 5 product categories by revenue (join `stg_cart_items` to `stg_products`, using a CTE).
2. Each user's most expensive cart, using `ROW_NUMBER()`.
3. Rank products by units sold with `RANK` and `DENSE_RANK`. Create a tie to see the difference.
4. Running total of revenue ordered by cart_id, plus the difference from the previous cart with `LAG`.
5. **Dedupe pattern:** insert a duplicate product with a newer `_loaded_at`, then keep only the latest:
   `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY _loaded_at DESC) = 1`

**Check yourself**
1. `WHERE` vs `HAVING`?
2. What do `ROW_NUMBER`, `RANK` and `DENSE_RANK` return for the tied values 100, 100, 90?
3. How do you dedupe and keep the latest record per key?
4. `LEFT JOIN b ... WHERE b.x = 1` vs `LEFT JOIN b ON ... AND b.x = 1`: what's the difference?

<details><summary>Answers</summary>

1. `WHERE` filters rows before grouping. `HAVING` filters groups after aggregation.
2. ROW_NUMBER 1,2,3 · RANK 1,1,3 · DENSE_RANK 1,1,2
3. `ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC) = 1`, using `QUALIFY` or a subquery or CTE.
4. Filtering in `WHERE` removes rows where `b` is NULL, which **silently turns it into an inner join**. Filtering in `ON` keeps all the rows from `a`.
</details>

---

## Day 37 — 🛠 Transform: build marts

**Do (40 min)**
1. `sql/marts/` files:
   - `mart_category_revenue.sql`: category, carts, units, gross revenue, discounted revenue
   - `mart_user_spend.sql`: user, number of carts, total spend, average cart value, rank
   - `mart_product_performance.sql`: product, units sold, revenue, average discount
   Each uses `CREATE OR REPLACE TABLE ... AS SELECT ...`
2. `transform.py`: run every `.sql` file in sorted order (`01_…`, `02_…`) and log the time and row count per mart.
3. Test: load a small set of hand-made rows into an in-memory DB, run one mart, and assert the exact numbers you calculated by hand.

**Check yourself**
1. Why keep SQL in `.sql` files instead of Python strings?
2. `CREATE OR REPLACE` (full rebuild) vs incremental: what's the trade-off?
3. What would dbt add to what you just built?
4. How do you test a SQL transformation?

<details><summary>Answers</summary>

1. Readability, editor support and linting, clean code reviews, and analysts can contribute.
2. A full rebuild is simple and always correct, but slow or expensive at scale. Incremental is fast but more complex (late data, dedupe, state).
3. Automatic dependency ordering (`ref()`), built-in tests, documentation and lineage, materialization strategies (table, view, incremental), and environments.
4. Small fixed input data → run the SQL → compare with expected output you calculated by hand.
</details>

---

## Day 38 — Parquet + Week 6 review 🔁

**Learn (10 min)**
- **Parquet:** a columnar file format with compression, an embedded schema and types. It's the standard of data lakes.
- **Partitioning:** `.../category=laptops/part-0.parquet`
- **Predicate/projection pushdown:** reading only the needed rows and columns.

**Do (25 min)**
1. `COPY mart_product_performance TO 'data/marts/product_performance.parquet' (FORMAT parquet)`
2. Export `stg_cart_items` partitioned by a column: `(FORMAT parquet, PARTITION_BY (_run_date))`
3. Compare the file sizes of JSON, CSV and Parquet for the same table. Write the numbers in the README.

**Weekly quiz**
1. Why is Parquet much smaller and faster to query than CSV?
2. What's the "small files problem"?
3. Explain idempotency in your load step in 2 sentences.
4. A dashboard shows doubled revenue for yesterday. Name 2 likely causes in a pipeline like yours.
5. Write (from memory) a query for the top customer per country, using a window function.

<details><summary>Answers</summary>

1. Columnar storage plus compression (similar values sit together), typed binary data with no parsing, and readers can skip columns and row groups.
2. Thousands of tiny files mean the overhead of opening files and reading metadata dominates, so queries get slow. Compact them into fewer, larger files (~100MB–1GB).
3. (Yours.) Each run replaces exactly its date partition inside a transaction, so reruns don't duplicate data.
4. A rerun that appended instead of replacing, or a join that fans out (one-to-many) and duplicates rows.
5. `SELECT * FROM t QUALIFY ROW_NUMBER() OVER (PARTITION BY country ORDER BY total DESC) = 1`
</details>

📝 Confidence log. Your pipeline now does real ELT. Update the README architecture diagram.

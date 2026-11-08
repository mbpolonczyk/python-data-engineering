# Week 8 · PySpark fundamentals

**Phase 4 — PySpark** · Days 44–48
[← Week 7](week-07-dataframes-quality.md) · [Plan overview](README.md) · [Week 9 →](week-09-pyspark-transformations.md)

> **This week's outcome:** you have a working Spark setup, you can explain how Spark runs your code (driver, executors, partitions, lazy evaluation), and you can read messy files with explicit schemas.
>
> **Project milestone:** `shopflow/src/shopflow/spark/staging.py` builds the same staging tables as your Week 6 DuckDB SQL, now in PySpark.

| Day | Topic | Time |
|---|---|---|
| 44 | Setup and the Spark mental model | ~60 min |
| 45 | DataFrame API and explicit schemas | ~45 min |
| 46 | Lazy evaluation, file formats, corrupt records | ~50 min |
| 47 | Aggregations, nested JSON, dates | ~50 min |
| 48 | 🛠 Build day: Spark staging + quiz | ~60 min |

You already know the hard part. Polars lazy frames (Week 7) work like Spark: you build a plan, and nothing runs until you ask for a result. Spark just runs that plan on many machines.

---

<a id="day-44"></a>
## Day 44 · Setup and the Spark mental model

⏱ ~60 min · 📁 `src/day44/hello_spark.py`

> 🎯 **By the end you can:** run Spark on your laptop and explain what the driver, executors, partitions, jobs, stages and tasks are.
> 💼 **At work:** "Explain how Spark executes a job" is the most common PySpark interview question.

### 📖 Learn (15 min)
- **Why Spark exists:** when the data doesn't fit on one machine, you split it into **partitions** and process them in parallel on many machines.
- **Driver:** your Python program. It builds the plan and coordinates. **Executors:** worker processes that run **tasks**, one task per partition.
- **Action → job → stages → tasks.** Each action (like `show()`) starts a **job**. Spark splits the job into **stages** wherever data must move between machines (a **shuffle**). Each stage runs one task per partition.
- `SparkSession` is your entry point: `spark.read`, `spark.sql`, `spark.createDataFrame`.
- **Spark UI** at http://localhost:4040 shows jobs, stages and tasks. It only exists while the session is running.
- Locally, `master("local[*]")` runs the driver and executors in one process, using every CPU core as a "machine".
- Docs: https://spark.apache.org/docs/latest/cluster-overview.html

### 💻 Do (35 min)
**Pick a setup.** On Windows, local Spark needs Java, and writing files needs extra Hadoop binaries (`winutils.exe`, `hadoop.dll`). These cause most beginner pain, so avoid native Windows.

| Option | Good for | Cost |
|---|---|---|
| **A · WSL2 + Java 17 + uv** ✅ recommended | the `shopflow` project, tests, Spark UI | free, ~20 min setup |
| **B · Docker** | if you already use Docker | free, needs Docker Desktop |
| **C · Databricks Free Edition** | quick practice in the browser | free account, no install |

- [ ] **1.** Set up **option A** (PowerShell as admin, then the Ubuntu terminal):
  ```powershell
  wsl --install -d Ubuntu
  ```
  ```bash
  sudo apt update && sudo apt install -y openjdk-17-jdk-headless
  java -version                       # should say 17
  curl -LsSf https://astral.sh/uv/install.sh | sh
  git clone <your-repo-url> ~/python-data-engineering   # keep code in the Linux filesystem: much faster than /mnt/c
  cd ~/python-data-engineering/shopflow && uv add "pyspark==4.0.*"
  ```
  Open the folder with `code .` (VS Code "WSL" extension). A `.venv` created on Windows won't work in Linux, so let uv create a new one there.
  *Option B:* `docker run -it --rm -p 8888:8888 -p 4040:4040 -v ${PWD}:/home/jovyan/work quay.io/jupyter/pyspark-notebook`, then open the Jupyter link it prints.
  *Option C:* sign up at https://www.databricks.com/learn/free-edition, create a notebook, and use the ready-made `spark` object. Note: it runs on serverless compute, so there's **no Spark UI, no `df.cache()` and no `spark.sparkContext`**. That's fine for days 45–47, but use A or B for the project and Week 10.
- [ ] **2.** Smoke test in `src/day44/hello_spark.py`:
  ```python
  from pyspark.sql import SparkSession
  spark = SparkSession.builder.master("local[*]").appName("hello").getOrCreate()
  df = spark.range(1_000_000)                      # one column: id
  print(df.selectExpr("sum(id)").first()[0])       # expect 499999500000
  print(df.rdd.getNumPartitions())                 # = number of cores
  df.write.mode("overwrite").parquet("/tmp/hello_parquet")   # proves writes work
  input("Open http://localhost:4040, then press Enter to stop")
  spark.stop()
  ```
  Run it with `uv run python src/day44/hello_spark.py`.
- [ ] **3.** In the Spark UI, open the **Jobs** tab. How many jobs ran? Click one and find its stages and the number of tasks. Write the numbers down as comments.
- [ ] **4.** Change the master to `local[2]` and run again. What changed in `getNumPartitions()` and in the task count?
- ⭐ *Stretch:* add `df.groupBy(df.id % 10).count().show()`. In the UI, this job has two stages. Why?

### ✅ Check yourself (5 min)
1. What's the difference between the driver and an executor?
2. How many tasks does a stage with 8 partitions run?
3. What creates a new stage?
4. Your teammate's Spark job is slow, and they want to "add more executors". When won't that help?

<details><summary>Answers</summary>

1. The driver runs your Python code, builds the plan and schedules tasks. Executors run the tasks on the data and hold the partitions.
2. 8: one task per partition.
3. A shuffle: an operation that needs rows from other partitions, like `groupBy`, `join` or `orderBy`.
4. When there are fewer partitions than cores (idle executors), when one partition is much bigger than the rest (skew, Week 10), or when the bottleneck is the driver (for example `collect()`).
</details>

---

<a id="day-45"></a>
## Day 45 · DataFrame API and explicit schemas

⏱ ~45 min · 📁 `src/day45/exercises45.py`

> 🎯 **By the end you can:** select, filter, add and cast columns, and define a schema with `StructType`.
> 💼 **At work:** an explicit schema is your data contract in Spark. It's the Week 5 pydantic model, but for millions of rows.

### 📖 Learn (10 min)
- `from pyspark.sql import functions as F, types as T`. Refer to columns with `F.col("price")`.
- `select`, `filter` (same as `where`), `withColumn("new", expr)`, `withColumnRenamed("old", "new")`, `drop`.
- Conditions: `F.when(cond, value).otherwise(other)`. Combine with `&`, `|`, `~` and **always wrap each condition in parentheses**.
- Casting: `F.col("price").cast("double")`. In Spark 4, **ANSI mode is on**: casting `"abc"` to a number raises an error. Use `F.col("price").try_cast("double")` (Spark 4) or `F.expr("try_cast(price AS DOUBLE)")` to get `null` instead.
- Schemas: `T.StructType([T.StructField("id", T.IntegerType()), ...])`, or a DDL string `"id INT, title STRING"`.
- Docs: https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html

### 💻 Do (30 min)
- [ ] **1.** Create this DataFrame with an explicit `StructType` (all `price` values are strings, as they arrive from a CSV):
  ```python
  rows = [(1, "Drill X200", "tools", "129.99", 14), (2, "Saw S1", "tools", "59.5", 0),
          (3, "Glove Pro", "safety", "abc", 120), (4, "Ladder 3m", "tools", None, 7),
          (5, "Helmet H", "safety", "24.00", 3)]
  # columns: product_id INT, title STRING, category STRING, price STRING, stock INT
  ```
  `df.printSchema()` and `df.show()`.
- [ ] **2.** Add `price_num` with `try_cast`. Then add `stock_status`: `"out"` if stock is 0, `"low"` if under 10, otherwise `"ok"`.
- [ ] **3.** Rename `title` to `product_name`, drop `price`, and keep only tools that are in stock. Expected: products 1 and 4.
- [ ] **4.** *Bug hunt:* this line fails. Read the error, explain why, and fix it:
  ```python
  df.filter(F.col("category") == "tools" & F.col("stock") > 0)
  ```
- [ ] **5.** Create the same DataFrame without a schema (`spark.createDataFrame(rows, ["product_id", "title", "category", "price", "stock"])`). Which types did Spark choose?
- ⭐ *Stretch:* add `price_gross = price_num * 1.23` rounded to 2 decimals, then cast it to `T.DecimalType(10, 2)`. Why do finance teams prefer decimals to doubles?

### ✅ Check yourself (5 min)
1. Why does `F.col("a") == 1 & F.col("b") == 2` go wrong?
2. Name two problems with `inferSchema=True` in production.
3. What's the difference between `cast` and `try_cast` in Spark 4?
4. A source adds a new column. With an explicit schema, what happens? Is that good or bad?

<details><summary>Answers</summary>

1. In Python, `&` binds more tightly than `==`, so it evaluates `1 & F.col("b")` first. Write `(F.col("a") == 1) & (F.col("b") == 2)`.
2. It reads the data an extra time to guess types (slow on big files), and it can guess wrong or differently each day: `"00123"` becomes `123`, or a column that's empty today becomes a string. Your types silently drift.
3. With ANSI mode on, `cast` raises an error on invalid input and `try_cast` returns `null`. Use `try_cast` only when you then **count or quarantine** the nulls.
4. The new column is ignored, so the job keeps working. That's good for stability, but you should still detect it (Week 5 schema drift) so you don't miss useful data.
</details>

---

<a id="day-46"></a>
## Day 46 · Lazy evaluation, file formats, corrupt records

⏱ ~50 min · 📁 `src/day46/exercises46.py`

> 🎯 **By the end you can:** tell transformations from actions, read a query plan, and capture corrupt records instead of losing them.
> 💼 **At work:** one `collect()` in the wrong place crashes the driver. One wrong read mode silently drops customer orders.

### 📖 Learn (15 min)
- **Transformations** (`select`, `filter`, `join`, `groupBy`) only build a plan and return instantly. **Actions** (`show`, `count`, `collect`, `write`, `toPandas`) run it. Same idea as polars `.lazy()` … `.collect()`.
- `df.explain(mode="formatted")` prints the physical plan. Look for `PushedFilters` and `ReadSchema` in the file scan.
- `collect()` and `toPandas()` copy **all rows into the driver's memory**, so big data crashes it. `count()` is safe for memory but runs a full job, and each action **recomputes the whole plan** from the files.
- Read modes for CSV/JSON: `PERMISSIVE` (default: bad rows kept, fields `null`, raw text in `_corrupt_record` **if that column is in your schema**), `DROPMALFORMED` (bad rows silently dropped), `FAILFAST` (error on the first bad row).
- Parquet stores the schema and is columnar, so Spark reads only the columns and row groups it needs.
- Docs: https://spark.apache.org/docs/latest/sql-data-sources-csv.html

### 💻 Do (30 min)
- [ ] **1.** Save as `src/day46/orders_bad.csv`:
  ```
  order_id,customer_id,amount,order_ts
  1,10,120.50,2026-03-01 10:15:00
  2,11,abc,2026-03-01 11:00:00
  3,12,80.00,2026-03-01 12:30:00
  4,10,45.00,2026-03-02 09:30:00
  ```
  Schema: `"order_id INT, customer_id INT, amount DOUBLE, order_ts TIMESTAMP, _corrupt_record STRING"`. Read it in each mode with `.option("mode", ...)` and `show(truncate=False)`. **Predict first**: how many rows does each mode return?
- [ ] **2.** In PERMISSIVE mode, split into `good` (`_corrupt_record` is null) and `bad`. Write `bad` to `/tmp/quarantine/orders/` as JSON. This is your Week 5 quarantine, Spark style. *(If Spark complains that a query references only the corrupt record column, call `df = df.cache()` after reading.)*
- [ ] **3.** Save as `src/day46/events_bad.jsonl` and read it with schema `"event_id INT, user_id INT, event_type STRING, ts TIMESTAMP, _corrupt_record STRING"`. Which rows are corrupt?
  ```
  {"event_id": 1, "user_id": 10, "event_type": "view", "ts": "2026-03-01T10:15:00Z"}
  {"event_id": 2, "user_id": 11, "event_type": "add_to_cart", "ts": "2026-03-01T10:16:00Z"}
  {"event_id": 3, "user_id": 12, "event_type": "view", "ts":
  {"event_id": 4, "user_id": "x", "event_type": "view", "ts": "2026-03-01T10:20:00Z"}
  ```
- [ ] **4.** Write `good` orders to Parquet, read them back, then run `.filter("amount > 100").select("order_id").explain(mode="formatted")`. Find `PushedFilters` and `ReadSchema`.
- [ ] **5.** *Explain why:* time each line of a 5-step transformation chain with `time.perf_counter()`. The transformations take ~0 ms and the final `show()` takes the time. Why?
- ⭐ *Stretch:* with DROPMALFORMED, compare `df.count()` with `len(df.collect())`. If they differ, find out why (hint: CSV column pruning).

### ✅ Check yourself (5 min)
1. Is `withColumn` a transformation or an action? And `write`?
2. Why is `toPandas()` on a 200 GB table a bad idea?
3. Which read mode do you use in production, and why not DROPMALFORMED?
4. You call `df.count()` then `df.show()` on an expensive pipeline. What happens twice?

<details><summary>Answers</summary>

1. `withColumn` is a transformation. `write` is an action.
2. All rows are copied to the driver's memory, which runs out. Aggregate or sample in Spark first, and only then convert the small result.
3. PERMISSIVE with a `_corrupt_record` column, then quarantine the bad rows and fail if there are too many. DROPMALFORMED loses data **with no trace**, so nobody knows orders are missing.
4. The whole plan runs twice, from reading the files onwards, because Spark doesn't keep results between actions unless you cache them (Week 10).
</details>

---

<a id="day-47"></a>
## Day 47 · Aggregations, nested JSON, dates

⏱ ~50 min · 📁 `src/day47/exercises47.py`

> 🎯 **By the end you can:** flatten nested arrays with `explode`, aggregate with `groupBy().agg()`, and work with dates and timestamps.
> 💼 **At work:** API data (like DummyJSON carts) is nested. Every report is an aggregation by some date.

### 📖 Learn (10 min)
- `df.groupBy("user_id").agg(F.sum("x").alias("total"), F.countDistinct("cart_id").alias("carts"))`
- Structs: `F.col("item.price")`. Arrays: `F.explode("products")` gives one row per element. **`explode` drops rows with empty or null arrays**; `explode_outer` keeps them.
- `F.size("products")` counts array elements. `F.inline("products")` explodes an array of structs straight into columns.
- Dates: `F.to_date`, `F.to_timestamp`, `F.try_to_timestamp` (null if invalid), `F.date_trunc("month", ts)`, `F.date_format(ts, "yyyy-MM")`, `F.datediff`.
- Set `spark.conf.set("spark.sql.session.timeZone", "UTC")` so timestamps don't depend on the machine.

### 💻 Do (35 min)
- [ ] **1.** Save these DummyJSON-style carts as `src/day47/carts.jsonl` and read them **without** a schema. Look at `printSchema()`:
  ```
  {"id": 1, "userId": 33, "date": "2026-03-01", "products": [{"id": 101, "title": "Drill X200", "price": 129.99, "quantity": 2, "discountPercentage": 10.0}, {"id": 102, "title": "Saw S1", "price": 59.5, "quantity": 1, "discountPercentage": 0.0}]}
  {"id": 2, "userId": 34, "date": "2026-03-01", "products": [{"id": 101, "title": "Drill X200", "price": 129.99, "quantity": 1, "discountPercentage": 5.0}]}
  {"id": 3, "userId": 33, "date": "2026-03-02", "products": []}
  ```
- [ ] **2.** Now write the explicit schema (`products` is `ArrayType(StructType([...]))`) and read again.
- [ ] **3.** Build `cart_items`: one row per product, with `cart_id`, `user_id`, `product_id`, `quantity`, `price` and `line_total = price * quantity * (1 - discountPercentage / 100)`. How many rows? Where did cart 3 go? Fix it with `explode_outer`.
- [ ] **4.** Revenue per user: `user_id`, `carts` (`countDistinct`), `units` (sum of quantity), `revenue` (rounded to 2). Expected for user 33: 2 carts, 3 units, revenue 293.48.
- [ ] **5.** Daily revenue: convert `date` with `F.to_date`, group by it, and add `day_of_week` with `F.date_format("cart_date", "EEEE")`.
- ⭐ *Stretch:* use `F.filter("products", lambda p: p["quantity"] > 1)` (a higher-order function) to keep only multi-unit items **without** exploding.

### ✅ Check yourself (5 min)
1. A cart with `products: []` disappears after your transformation. Why?
2. What's the grain (one row per what?) before and after `explode`?
3. Why should you aggregate `cart_items` revenue per cart and not trust the `total` field from the API?
4. Why set the session time zone to UTC?

<details><summary>Answers</summary>

1. `explode` produces no rows for empty or null arrays. Use `explode_outer` if the parent row must survive.
2. Before: one row per cart. After: one row per product **within** a cart. Summing cart-level columns after the explode double-counts them.
3. You can test your own calculation, and it stays consistent with the items you actually loaded. Comparing the two is a good data-quality check.
4. Timestamp parsing and `to_date` use the session time zone. Without a fixed one, the same job gives different dates on a laptop and on a cluster.
</details>

---

<a id="day-48"></a>
## Day 48 · 🛠 Build day: Spark staging + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/spark/`

> 🎯 **By the end you can:** turn shopflow's raw files into typed staging Parquet with Spark, and prove it matches DuckDB.
> 💼 **At work:** "rewrite this pandas/SQL job in Spark" is a very common migration task.

### 💻 Do (45 min)
- [ ] **1.** `spark/session.py`: `get_spark(app_name: str) -> SparkSession` with `local[*]`, `spark.sql.session.timeZone=UTC` and `spark.sql.shuffle.partitions=8` (the default of 200 is far too many for small data).
- [ ] **2.** `spark/schemas.py`: one explicit schema per raw entity (products, users, carts, ERP orders, supplier prices, clickstream), each with `_corrupt_record STRING`. Copy the field names from your Week 5 pydantic models.
- [ ] **3.** `spark/staging.py`: one function per entity, e.g. `stage_carts(spark, raw_path) -> DataFrame`. Read `data/raw/<source>/<entity>/` (Spark turns the `load_date=…` folders into a `load_date` column automatically), rename to snake_case, cast types, add `_loaded_at = F.current_timestamp()`, quarantine corrupt rows, and write Parquet to `data/staging/<table>/`. Use the same table and column names as your Week 6 DuckDB staging.
- [ ] **4.** Dedupe on the business key with `dropDuplicates(["order_id"])` for now. It keeps an **arbitrary** row; Day 50 fixes that properly.
- [ ] **5.** Compare with DuckDB: read both versions of `stg_erp__orders` in Spark and run `spark_df.exceptAll(duck_df).count()` both ways. Both should be 0. Investigate any difference (types? time zones? rounding?).
- [ ] **6.** Fill in **playbook §5** with: explicit schema + corrupt-record handling in Spark, and why `dropDuplicates` isn't enough.

### ✅ Weekly quiz
1. *Explain out loud, as in an interview:* what happens, step by step, when you call `df.groupBy("user_id").count().show()`?
2. Why use explicit schemas instead of `inferSchema` in production?
3. Which of these are actions: `filter`, `collect`, `explode`, `write`, `count`?
4. How do you keep corrupt rows instead of dropping them?
5. What's the difference between `explode` and `explode_outer`?

<details><summary>Answers</summary>

1. The driver builds a logical plan, optimizes it and turns it into a physical plan. `show()` is an action, so a job starts. Stage 1 reads the partitions and does a partial count per partition, then **shuffles** rows by `user_id`. Stage 2 adds up the partial counts per user. Only the first 20 rows go back to the driver.
2. They're faster (no extra pass), stable (types can't drift), and they act as a contract: unexpected data fails loudly or lands in `_corrupt_record`.
3. `collect`, `write`, `count`.
4. PERMISSIVE mode with `_corrupt_record STRING` in the schema. Then split good and bad rows, and quarantine the bad ones.
5. `explode` drops rows whose array is empty or null. `explode_outer` keeps them, with `null` in the exploded column.
</details>

---

## 🏁 End of week 8: I can…
- [ ] Run Spark locally and find jobs, stages and tasks in the Spark UI
- [ ] Explain driver, executors, partitions and lazy evaluation
- [ ] Read CSV/JSON/Parquet with explicit schemas and quarantine corrupt records
- [ ] Flatten nested JSON and aggregate it

📈 Rate your confidence for Week 8 in the [progress tracker](README.md#-progress-tracker).

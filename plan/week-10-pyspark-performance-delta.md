# Week 10 · PySpark performance and Delta Lake

**Phase 4 — PySpark** · Days 54–58
[← Week 9](week-09-pyspark-transformations.md) · [Plan overview](README.md) · [Week 11 →](week-11-production.md)

> **This week's outcome:** you can read a query plan and the Spark UI, fix the usual performance problems (shuffles, skew, small files), and load data incrementally into Delta Lake with `MERGE`.
>
> **Project milestone:** shopflow runs raw → staging (Delta, `MERGE`) → marts incrementally, and a rerun gives exactly the same result.

| Day | Topic | Time |
|---|---|---|
| 54 | Partitions and shuffles | ~50 min |
| 55 | Join performance, skew and caching | ~50 min |
| 56 | Writing data: partitioning and small files | ~50 min |
| 57 | Delta Lake: `MERGE`, time travel, schema | ~60 min |
| 58 | 🛠 Build day: incremental pipeline + perf review + quiz | ~60 min |

Use **option A or B** from Day 44 this week. You need the Spark UI, and Databricks Free Edition doesn't have it.

---

<a id="day-54"></a>
## Day 54 · Partitions and shuffles

⏱ ~50 min · 📁 `src/day54/exercises54.py`

> 🎯 **By the end you can:** tell narrow from wide transformations, find shuffles in a plan and the UI, and choose between `repartition` and `coalesce`.
> 💼 **At work:** shuffles are where most Spark time and cost go. "Where's the shuffle?" is the first question in any tuning session.

### 📖 Learn (15 min)
- **Narrow** transformations work inside each partition: `select`, `filter`, `withColumn`. **Wide** ones need rows from other partitions, so they **shuffle** (write to disk, send over the network): `groupBy`, `join`, `distinct`, `orderBy`, windows with `partitionBy`.
- In `explain()`, a shuffle is an `Exchange`. In the UI, each shuffle starts a new stage, and the Stages tab shows **Shuffle Write** and **Shuffle Read**.
- `spark.sql.shuffle.partitions` (default 200) sets how many partitions a shuffle produces. Too many means tiny tasks; too few means huge tasks that spill to disk.
- **AQE** (Adaptive Query Execution, on by default since Spark 3.2) adjusts the plan at runtime, for example by merging small shuffle partitions.
- `repartition(n)` or `repartition("col")`: a full shuffle into even partitions. `coalesce(n)`: merges partitions **without** a shuffle; it can only reduce them, and the result can be uneven.
- Docs: https://spark.apache.org/docs/latest/sql-performance-tuning.html

### 💻 Do (30 min)
- [ ] **1.** Classify as narrow or wide: `filter`, `groupBy().sum()`, `withColumn`, `join` (two big tables), `orderBy`, `dropDuplicates`, `select`, `union`.
- [ ] **2.** Turn AQE off for now (`spark.conf.set("spark.sql.adaptive.enabled", "false")`) and run:
  ```python
  big = (spark.range(20_000_000)
         .withColumn("customer_id", F.col("id") % 1000)
         .withColumn("amount", F.rand(seed=1) * 100))
  agg = big.groupBy("customer_id").agg(F.sum("amount").alias("total"))
  agg.explain(mode="formatted")
  agg.write.format("noop").mode("overwrite").save()
  ```
  Find the `Exchange` in the plan. In the UI: how many stages, how many tasks in the second one, and how big is the shuffle write?
- [ ] **3.** Set `spark.sql.shuffle.partitions` to `8` and rerun. Then set AQE back on with 200 partitions. Look for `AQEShuffleRead` / "coalesced" in the SQL tab. What did AQE do?
- [ ] **4.** *Predict, then check:* `big.coalesce(1).write.format("noop").mode("overwrite").save()` vs `big.repartition(1)...`. How many tasks does the stage that **generates** the data run in each case? Why?
- ⭐ *Stretch:* use `F.spark_partition_id()` to count rows per partition after `repartition(8, "customer_id")`.

### ✅ Check yourself (5 min)
1. Why is a shuffle expensive?
2. You have 1,000 cores and `shuffle.partitions = 200`. What's the problem?
3. `coalesce(1)` before a write made the whole job slow. Why?
4. When do you `repartition` on purpose?

<details><summary>Answers</summary>

1. Rows are serialized, written to local disk, sent over the network and read back by other executors. That's disk, network and CPU at once.
2. At most 200 tasks run at a time, so 800 cores sit idle after each shuffle. Raise the setting, or let AQE work from a higher starting value.
3. `coalesce` doesn't add a shuffle, so Spark merges the partitions **upstream**: the whole stage, reading and transforming included, runs as one task. `repartition(1)` keeps the upstream stage parallel and only funnels the final write.
4. Before a write, to control the number of output files (Day 56); to fix badly uneven partitions; or to co-locate rows by a key that several later steps use.
</details>

---

<a id="day-55"></a>
## Day 55 · Join performance, skew and caching

⏱ ~50 min · 📁 `src/day55/exercises55.py`

> 🎯 **By the end you can:** force or avoid a broadcast join, spot data skew in the UI, and decide when caching helps.
> 💼 **At work:** "one task runs for an hour while the others finish in seconds" is skew, and it's one of the most asked-about Spark problems.

### 📖 Learn (15 min)
- **Sort-merge join:** both sides are shuffled by the key. **Broadcast hash join:** the small side is copied to every executor, so the big side doesn't move at all.
- Spark broadcasts automatically below `spark.sql.autoBroadcastJoinThreshold` (default 10 MB). Force it with `big.join(F.broadcast(small), "key")`. Broadcasting something large can crash the driver or executors with out-of-memory errors.
- **Skew:** a few keys hold most of the rows (e.g. one marketplace seller, or `customer_id = null`). One task gets most of the work. In the UI's stage page, compare **max** and **median** task duration.
- Fixes: AQE skew join (`spark.sql.adaptive.skewJoin.enabled`, on by default) splits big partitions; broadcasting the small side; handling null keys separately; **salting**.
- `df.cache()` is lazy: it stores the data on the next action. It helps when the same DataFrame is used **several times**. Call `unpersist()` when you're done.

### 💻 Do (30 min)
- [ ] **1.** Set `spark.sql.adaptive.enabled` to `false` and `spark.sql.autoBroadcastJoinThreshold` to `-1`. Then compare plans:
  ```python
  facts = spark.range(10_000_000).withColumn("product_id", F.col("id") % 1000)
  dim = spark.range(1000).withColumnRenamed("id", "product_id").withColumn("category", F.lit("tools"))
  facts.join(dim, "product_id").explain()               # look for SortMergeJoin
  facts.join(F.broadcast(dim), "product_id").explain()  # look for BroadcastHashJoin
  ```
  Time both with a `noop` write. How many `Exchange`s does each plan have?
- [ ] **2.** Create skew: 90% of rows get `product_id = 1`:
  ```python
  skewed = spark.range(10_000_000).withColumn(
      "product_id", F.when(F.rand(seed=7) < 0.9, F.lit(1)).otherwise(F.col("id") % 1000))
  ```
  Join it to `dim` without a broadcast. In the UI, open the join stage and compare the max and median task duration and shuffle read size.
- [ ] **3.** Turn AQE on and rerun. Look in the SQL tab for a skew-join note. *(Locally it may not trigger: the default threshold is 256 MB per partition. You can lower `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` to experiment.)*
- [ ] **4.** Caching: build an expensive `order_lines` (your Day 49 joins) and use it for **three** aggregations. Time it without and with `.cache()`. Check the **Storage** tab, then `unpersist()`.
- ⭐ *Stretch:* sketch salting for the skewed join in comments, then try it.
  <details><summary>Hint (only after you've tried)</summary>

  Add `salt = (F.rand() * N).cast("int")` to the big side. Cross-join the small side with `spark.range(N)` as `salt`, so each key exists N times. Join on `product_id` **and** `salt`. The hot key is now spread over N tasks.
  </details>

### ✅ Check yourself (5 min)
1. Why is a broadcast join faster?
2. How do you spot skew in the Spark UI?
3. Give two cases where caching makes things worse.
4. Your job joins orders to customers, and 30% of orders have `customer_id = null`. What happens, and how do you fix it?

<details><summary>Answers</summary>

1. The big side isn't shuffled at all. Each executor joins its own partitions against a local copy of the small table.
2. On the stage page, the max task duration (and shuffle read) is far above the median, and the stage waits on a few last tasks.
3. A DataFrame used only once (you pay for storing it and get nothing back); a DataFrame too big for memory (it spills or evicts other data); caching **before** a filter that would have cut most rows.
4. All null keys hash to the same partition, so one task gets 30% of the data, and none of those rows will match anyway. Split them off, join only the non-null rows, then `union` the nulls back (with null customer columns).
</details>

---

<a id="day-56"></a>
## Day 56 · Writing data: partitioning and small files

⏱ ~50 min · 📁 `src/day56/exercises56.py`

> 🎯 **By the end you can:** choose partition columns, control the number of files, and rerun one day without touching the others.
> 💼 **At work:** "the table has 2 million tiny files and every query is slow" is a real ticket you'll get. So is "the rerun deleted last month".

### 📖 Learn (10 min)
- Write modes: `errorifexists` (default), `append`, `overwrite`, `ignore`.
- `partitionBy("order_date")` creates `order_date=2026-03-01/` folders. Readers that filter on that column skip the other folders (**partition pruning**).
- Good partition columns have **low cardinality** and match common filters (usually a date). Partitioning by `customer_id` creates thousands of folders with tiny files: **over-partitioning**.
- Files per folder = in-memory partitions that contain that value. Many small files make reads slow. Aim for roughly 128 MB–1 GB per file. Tools: `repartition("order_date")` before the write, `maxRecordsPerFile`.
- Plain `overwrite` with `partitionBy` deletes the **whole table**. `spark.sql.sources.partitionOverwriteMode=dynamic` only replaces the partitions present in your DataFrame. That's Week 6's idempotent delete + insert, per partition.

### 💻 Do (35 min)
- [ ] **1.** Make 1M orders over 30 days:
  ```python
  orders = (spark.range(1_000_000)
            .withColumn("order_date", F.date_add(F.lit("2026-03-01").cast("date"), (F.col("id") % 30).cast("int")))
            .withColumn("customer_id", F.col("id") % 2000)
            .withColumn("amount", F.round(F.rand(seed=3) * 200, 2))
            .repartition(8))
  ```
  Write with `partitionBy("order_date")` to `/tmp/orders_a`. Count the files: `len(list(Path("/tmp/orders_a").rglob("*.parquet")))`. Predict first: up to how many?
- [ ] **2.** Write again with `.repartition("order_date")` before `partitionBy`. How many files now, and why?
- [ ] **3.** Write with `partitionBy("customer_id")`. Time it and count folders and files. Write one sentence on why this is a bad choice.
- [ ] **4.** *Bug hunt:* rerun one day like this, then count rows per date in `/tmp/orders_a`. What happened?
  ```python
  fixed_day = orders.filter(F.col("order_date") == "2026-03-02")
  fixed_day.write.mode("overwrite").partitionBy("order_date").parquet("/tmp/orders_a")
  ```
  Rebuild the table, set `partitionOverwriteMode` to `dynamic`, and try again.
- ⭐ *Stretch:* read `/tmp/orders_a` with a filter on `order_date` and find `PartitionFilters` in `explain()`.

### ✅ Check yourself (5 min)
1. Why is `order_date` usually a better partition column than `customer_id`?
2. What causes the small-files problem, and why does it hurt?
3. What does dynamic partition overwrite do, and why does it make reruns safe?
4. A daily job appends to a table, and it ran twice yesterday after a retry. What's wrong now, and what should the write look like?

<details><summary>Answers</summary>

1. It has few values (one folder a day), and most queries filter by date, so pruning works. `customer_id` has many values, which means thousands of tiny folders.
2. Many write tasks each write a little to many partition folders. Every file costs metadata calls and an open/read on every query, so listing and opening files takes longer than reading the data.
3. It replaces only the partitions that appear in the DataFrame you write. Rerunning a day replaces that day, exactly once, and leaves other days alone.
4. Yesterday's rows are duplicated. Use overwrite with dynamic partition mode for the run's date (or a Delta `MERGE`/`replaceWhere`), so a rerun replaces data instead of adding it.
</details>

---

<a id="day-57"></a>
## Day 57 · Delta Lake: `MERGE`, time travel, schema

⏱ ~60 min · 📁 `src/day57/exercises57.py`

> 🎯 **By the end you can:** upsert incremental orders with `MERGE`, read old versions, and control schema changes.
> 💼 **At work:** Delta Lake (or Iceberg, which is similar) is the standard table format on Databricks and most lakehouses.

### 📖 Learn (15 min)
- Delta = Parquet files + a transaction log (`_delta_log/`). That gives you **ACID** writes (readers never see half a write), `MERGE`, `UPDATE`/`DELETE`, and history.
- **Versions must match Spark:** Delta 4.0.x for Spark 4.0, Delta 3.2–3.3 for Spark 3.5. Check the table at https://docs.delta.io/releases/. On Databricks, Delta is built in.
- **`MERGE`** upserts: match source rows to target rows on a key, update the matches and insert the rest. Each target row may match **at most one** source row, so dedupe the source first (`latest_by_key`, Day 50).
- **Time travel:** `spark.read.format("delta").option("versionAsOf", 0).load(path)`. `DeltaTable.forPath(spark, path).history()` lists the versions.
- **Schema enforcement:** an append with extra or different columns fails. **Evolution** is opt-in: `.option("mergeSchema", "true")`.
- `OPTIMIZE` compacts small files (Day 56's problem). `VACUUM` deletes old files no longer in the log (default retention: 7 days), and after that you can't time-travel past it.

### 💻 Do (40 min)
- [ ] **1.** Setup: `uv add "delta-spark==4.0.*"` (match your PySpark version), then:
  ```python
  from delta import configure_spark_with_delta_pip
  from delta.tables import DeltaTable
  builder = (SparkSession.builder.master("local[*]").appName("delta")
      .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
      .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"))
  spark = configure_spark_with_delta_pip(builder).getOrCreate()   # first run downloads a jar: needs internet
  ```
- [ ] **2.** Write the target to `/tmp/delta/orders` with `.format("delta")` (cast `updated_at` to a timestamp first): `(1, "paid", 120.0, "2026-03-01 12:00:00")`, `(2, "pending", 80.0, "2026-03-01 11:00:00")`, `(3, "paid", 45.0, "2026-03-02 10:00:00")`.
- [ ] **3.** Incoming batch: `(2, "shipped", 80.0, "2026-03-03 08:00:00")`, `(4, "paid", 60.0, "2026-03-03 09:00:00")`, `(3, "pending", 45.0, "2026-03-01 09:00:00")` (a stale update). Merge it, updating only when the source row is newer:
  ```python
  (DeltaTable.forPath(spark, "/tmp/delta/orders").alias("t")
      .merge(batch.alias("s"), "t.order_id = s.order_id")
      .whenMatchedUpdateAll(condition="s.updated_at > t.updated_at")
      .whenNotMatchedInsertAll()
      .execute())
  ```
  Expected: 4 rows, order 2 `shipped`, order 3 still `paid`. **Run the merge again.** Still the same 4 rows?
- [ ] **4.** Add a duplicate of order 4 to the batch and merge. Read the error, then fix it with `latest_by_key` before the merge.
- [ ] **5.** Look at `history()`, then read version 0. Append a DataFrame with an extra `channel` column: read the error, then retry with `mergeSchema`.
- [ ] **6.** Watermark (Week 4): read `max(updated_at)` from the Delta table and only take raw rows newer than it. Why might you subtract a small **lookback** (e.g. 1 hour), and why is that safe with this `MERGE`?
- [ ] **7.** Fill in **playbook §5**: your `MERGE` strategy, the dedupe before it, and how late or updated records are handled.

### ✅ Check yourself (5 min)
1. What does the `_delta_log` folder give you that plain Parquet doesn't?
2. Why is the `MERGE` above idempotent?
3. Schema enforcement vs schema evolution: when do you use each?
4. Someone runs `VACUUM` with zero retention to save storage. What breaks?

<details><summary>Answers</summary>

1. Atomic commits (a failed job leaves no partial data), a consistent snapshot for readers, the history and time travel, and row-level operations like `MERGE`, `UPDATE` and `DELETE`.
2. A matched row is only updated when the source is newer. Replaying the same batch matches the same keys, finds nothing newer, and inserts nothing new.
3. Enforcement by default, so unexpected changes fail loudly (Week 5 drift). Evolution deliberately, when you've decided to accept a new column, ideally after a drift alert and a review.
4. Time travel to older versions, and any reader or job still using older files. Delta blocks short retention by default for this reason.
</details>

---

<a id="day-58"></a>
## Day 58 · 🛠 Build day: incremental pipeline + perf review + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/spark/pipeline.py`

> 🎯 **By the end you can:** run an incremental, rerun-safe Spark pipeline and review its performance like a senior engineer.
> 💼 **At work:** this is the shape of most production lakehouse jobs.

### 💻 Do (45 min)
- [ ] **1.** Add the Delta config to `get_spark()` (Day 48). In `pipeline.py`, write `run(spark, run_date)`:
  - ERP orders: read raw → `transform_orders` → `latest_by_key` → `MERGE` into `data/delta/stg_erp__orders`, using the watermark with a lookback (Day 57).
  - Small sources (products, users, supplier prices): full overwrite as Delta.
  - Marts: build them with `marts.py` (Day 53) and overwrite, or use `replaceWhere` to replace only the affected dates.
- [ ] **2.** Before writing the marts, run quality checks: rows > 0, unique `order_id` in staging, no null `order_date`. Reuse the rules from your Week 7 `checks.py`, and fail the run if one breaks.
- [ ] **3.** Rerun test: run the pipeline twice for the same date and assert that every table has the same row count and contents (`exceptAll` both ways). Put it in `tests/spark/test_pipeline.py`.
- [ ] **4.** Perf review of your own job, written up in the shopflow README:
  - `explain(mode="formatted")` per mart: how many `Exchange`s? Are the small tables broadcast? Any `BatchEvalPython`?
  - Spark UI: the slowest stage, max vs median task time, shuffle sizes.
  - File count per table, and whether `OPTIMIZE` would help.
  - One change you made, and the before/after time.

### ✅ Weekly quiz
1. *Explain out loud, as in an interview:* how do you load an incremental source into a lakehouse table so that reruns and late updates are safe?
2. When does Spark use a broadcast join, and when is it dangerous?
3. `repartition` vs `coalesce`?
4. What's the small-files problem, and two ways to fix it?
5. How do you spot data skew, and name two fixes.

<details><summary>Answers</summary>

1. Extract rows newer than the watermark minus a small lookback, dedupe them to the latest version per key, then `MERGE` into a Delta table, updating only when the source is newer. Rereading rows is harmless because the `MERGE` is idempotent, and the lookback catches late arrivals.
2. When the smaller side is below `autoBroadcastJoinThreshold` (10 MB by default), or when you hint `F.broadcast`. It's dangerous when the "small" table is actually large, because every executor (and the driver) must hold a copy, which can cause out-of-memory errors.
3. `repartition` does a full shuffle and can increase or decrease partitions evenly. `coalesce` only decreases them, without a shuffle, but can make partitions uneven and reduce upstream parallelism.
4. Too many tiny files make listing and reading slow. Fix it by repartitioning by the partition column before writing, by choosing a lower-cardinality partition column, or by compacting with Delta `OPTIMIZE`.
5. In the stage page of the UI, max task time or shuffle read is far above the median. Fixes: AQE skew join, broadcasting the small side, handling null or hot keys separately, salting.
</details>

---

## 🎓 Phase 4 wrap-up: PySpark interview questions you can now answer

1. Explain driver, executors, partitions, jobs, stages and tasks. *(Day 44)*
2. Transformations vs actions: why is Spark lazy, and why is `collect()` dangerous? *(Day 46)*
3. How do you handle corrupt records and schema drift when reading files? *(Days 45–46)*
4. How do you dedupe to the latest record per key? *(Day 50)*
5. Why are Python UDFs slow, and what do you use instead? *(Day 51)*
6. How do you unit-test PySpark code? *(Day 52)*
7. Narrow vs wide transformations: what's a shuffle, and how do you reduce it? *(Day 54)*
8. Broadcast vs sort-merge join; how do you detect and fix skew? *(Day 55)*
9. How do you choose partition columns, and what's the small-files problem? *(Day 56)*
10. How do you make an incremental load idempotent with Delta `MERGE`? *(Days 57–58)*

Ask Claude: **"Interview me on Phase 4 PySpark. One question at a time, and push back on vague answers."**

---

## 🏁 End of week 10: I can…
- [ ] Find shuffles in `explain()` and the Spark UI, and tune shuffle partitions
- [ ] Use broadcast joins, and spot and fix skew
- [ ] Write partitioned data without small files, and rerun one partition safely
- [ ] Upsert incremental data with Delta `MERGE`, and use time travel

📈 Rate your confidence for Week 10 in the [progress tracker](README.md#-progress-tracker).

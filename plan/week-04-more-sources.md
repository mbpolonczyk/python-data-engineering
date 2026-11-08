# Week 4 · Databases, files and object storage as sources

**Phase 2 — Integrating new data sources** · Days 24–28
[← Week 3](week-03-rest-apis.md) · [Plan overview](README.md) · [Week 5 →](week-05-validation.md)

> **This week's outcome:** you can extract from a database incrementally, tame messy supplier files, read from S3, and speed up I/O-heavy extraction with threads, all behind one common connector interface.
>
> **Project milestone:** `shopflow` gets three new sources (SQLite "ERP", supplier price files, S3 clickstream), a shared `Connector` interface and one runner that lands them all in raw.

| Day | Topic | Time |
|---|---|---|
| 24 | A database as a source: incremental extraction with a watermark | ~55 min |
| 25 | Messy files: Excel, `;` CSVs, decimal commas, cp1250 | ~50 min |
| 26 | Object storage (S3 with moto) + context managers and atomic writes | ~55 min |
| 27 | Concurrency for extraction: threads and rate limits | ~50 min |
| 28 | 🛠 Build day: one connector interface for every source + quiz | ~60 min |

---

<a id="day-24"></a>
## Day 24 · A database as a source: incremental extraction with a watermark

⏱ ~55 min · 📁 `shopflow/scripts/seed_erp.py`, `shopflow/src/shopflow/sources/erp.py`

> 🎯 **By the end you can:** pull only new or changed rows from a database with safe, parameterised SQL, and remember where you stopped.
> 💼 **At work:** nobody lets you `SELECT *` a 200-million-row ERP table every night. Incremental loads are the default.

### 📖 Learn (15 min)
- `sqlite3` is built in: `con = sqlite3.connect(path)`, `con.row_factory = sqlite3.Row` (rows behave like dicts), `con.execute(sql, params)`.
- **Parameterised queries:** `WHERE updated_at > ?` with `(watermark,)`. Never build SQL with f-strings from input: that's SQL injection, and it also breaks on quotes.
- **Full load:** take everything, every time. Simple, but slow and expensive. **Incremental:** `WHERE updated_at > :watermark`, then save the new max `updated_at` as the next watermark.
- Save the watermark **only after** the data is safely written. Otherwise a crash loses rows forever.
- Iterate the cursor (`for row in cur:`) or use `fetchmany(1000)`. `fetchall()` loads everything into memory.
- Docs: https://docs.python.org/3/library/sqlite3.html

### 💻 Do (35 min)
- [ ] **1.** Create `shopflow/scripts/seed_erp.py` and run it with `uv run python scripts/seed_erp.py` (from `shopflow/`):
  ```python
  import random, sqlite3
  from datetime import datetime, timedelta
  from pathlib import Path

  db = Path("data/erp.db")
  db.parent.mkdir(parents=True, exist_ok=True)
  con = sqlite3.connect(db)
  con.executescript("""
  DROP TABLE IF EXISTS orders;
  CREATE TABLE orders (
      order_id    INTEGER PRIMARY KEY,
      customer_id INTEGER NOT NULL,
      product_id  INTEGER NOT NULL,  -- matches DummyJSON product ids
      quantity    INTEGER NOT NULL,
      amount      REAL    NOT NULL,
      currency    TEXT    NOT NULL,  -- 'EUR' (you'll convert to PLN in Week 12)
      status      TEXT    NOT NULL,
      updated_at  TEXT    NOT NULL   -- ISO 8601, UTC
  );
  """)
  random.seed(42)
  start = datetime(2026, 10, 1)
  rows = []
  for i in range(1, 201):
      qty = random.randint(1, 5)
      rows.append((i, random.randint(1, 50), random.randint(1, 30), qty,
                   round(qty * random.uniform(5, 300), 2), "EUR",
                   random.choice(["new", "paid", "shipped", "cancelled"]),
                   (start + timedelta(hours=3 * i)).isoformat(timespec="seconds")))
  con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
  con.commit()
  con.close()
  ```
- [ ] **2.** In `erp.py`: `extract_orders(db_path, since: str | None) -> Iterator[dict]`. `None` means a full load. Order by `updated_at`.
- [ ] **3.** State: `load_watermark(path) -> str | None` and `save_watermark(path, value)` using `data/state/erp_orders.json` (`{"watermark": "2026-10-20T07:00:00"}`).
- [ ] **4.** Run it: the first run takes 200 rows. Run again: 0 rows. Now simulate the ERP changing:
  ```sql
  UPDATE orders SET status = 'shipped', updated_at = '2026-11-03T09:00:00' WHERE order_id IN (5, 17, 42);
  ```
  (run it with `con.execute(...)` and `con.commit()`). Third run: exactly 3 rows.
- [ ] **5.** *Bug hunt:* why is this dangerous? Fix it.
  ```python
  con.execute(f"SELECT * FROM orders WHERE status = '{status}'")
  ```
  Try it with `status = "x' OR '1'='1"`.
- [ ] **6.** 📘 Add the watermark pattern and its gotchas to **§2 Extract** in your [playbook](new-source-playbook.md#2--extract).
- ⭐ *Stretch:* add a `--full` option that ignores the watermark. When would you need it?

### ✅ Check yourself (5 min)
1. Why save the watermark *after* writing the data and not before?
2. `updated_at > ?` vs `updated_at >= ?`: what's the trade-off?
3. Can a watermark on `updated_at` catch **deleted** rows?
4. When is a full load the better choice?

<details><summary>Answers</summary>

1. If the job crashes after saving the watermark but before writing, the next run starts after rows you never stored. They're lost silently.
2. `>` can miss rows committed later with the same timestamp as the watermark. `>=` re-reads the boundary rows, so you get duplicates, but staging dedupes them by key (Week 6). Many teams use `>=` or a small lookback window and dedupe downstream.
3. No. Deleted rows don't get a new `updated_at`. You need soft deletes (`is_deleted`), change data capture (CDC), or a periodic full comparison.
4. Small tables, tables with no reliable change column, or when you must catch deletes. Also for backfills and repairs.
</details>

---

<a id="day-25"></a>
## Day 25 · Messy files: Excel, `;` CSVs, decimal commas, cp1250

⏱ ~50 min · 📁 `shopflow/scripts/make_supplier_files.py`, `src/day25/exercises25.py`

> 🎯 **By the end you can:** read the kind of files EU suppliers really send, without corrupting Polish characters or prices.
> 💼 **At work:** "1 249,00" read as text, or "Piła" turned into "PiĹ‚a", is a real bug that reaches finance reports.

### 📖 Learn (10 min)
- `cd shopflow; uv add pandas openpyxl`
- `pd.read_csv(path, sep=";", decimal=",", thousands=" ", encoding="cp1250")`. Excel in Poland exports CSVs with `;` and decimal commas, often in cp1250.
- **Encoding traps:** reading cp1250 as UTF-8 raises `UnicodeDecodeError`, which is good, because it's loud. Reading it as `latin-1` never fails but silently gives wrong letters.
- `pd.read_excel(path, sheet_name=None, skiprows=3)` returns `{sheet_name: DataFrame}` for every sheet. `dtype=str` keeps values exactly as written.
- Docs: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html

### 💻 Do (35 min)
- [ ] **1.** Create the supplier files with this script (run from `shopflow/`):
  ```python
  from pathlib import Path
  import pandas as pd

  out = Path("data/landing/supplier"); out.mkdir(parents=True, exist_ok=True)
  rows = [("WIERT-01", "Wiertarka udarowa 750W", "349,99", "szt."),
          ("PILA-07", "Piła łańcuchowa spalinowa", "1 249,00", "szt."),
          ("KLUCZ-12", "Klucz dynamometryczny 1/2 cala", "89,50", "szt."),
          ("ZAR-03", "Żarówka LED E27 (10 szt.)", "45,00", "opak.")]
  with open(out / "prices_2026-11-03.csv", "w", encoding="cp1250", newline="") as f:
      f.write("kod;nazwa;cena_netto;jednostka\n")
      f.writelines(";".join(r) + "\n" for r in rows)

  def sheet(xw, name, df):
      pd.DataFrame([["Cennik dostawcy ABC"], ["Ceny netto PLN"]]).to_excel(
          xw, sheet_name=name, index=False, header=False)
      df.to_excel(xw, sheet_name=name, index=False, startrow=3)

  with pd.ExcelWriter(out / "prices_2026-11-03.xlsx", engine="openpyxl") as xw:
      sheet(xw, "Elektronarzedzia", pd.DataFrame({"kod": ["WIERT-01", "PILA-07"], "cena_netto": [349.99, 1249.0]}))
      sheet(xw, "Ogrod", pd.DataFrame({"kod": ["KOS-02"], "cena_netto": [899.0]}))
  ```
- [ ] **2.** Read the CSV with plain `pd.read_csv(path)`. What goes wrong? Then try `encoding="utf-8"`, then `encoding="latin-1"`. Write down what each one does.
- [ ] **3.** Read it correctly and check `df["cena_netto"].dtype` is `float64` and "Piła" looks right.
- [ ] **4.** Read **both sheets** of the Excel file in one call and combine them into one DataFrame with a `sheet` column (`pd.concat`).
- [ ] **5.** Now read the CSV again with `dtype=str` and keep `cena_netto` as `"1 249,00"`. Explain in a comment why the *raw* layer should keep the text, and the *staging* layer should convert it.
- ⭐ *Stretch:* real Excel exports often use a non-breaking space (`"\xa0"`) as the thousands separator. What breaks, and how would you handle it?

### ✅ Check yourself (5 min)
1. Why is a `UnicodeDecodeError` better than a file that "reads fine" with `latin-1`?
2. What do `decimal=","` and `thousands=" "` do?
3. What does `sheet_name=None` return?
4. A supplier changes their file from cp1250 to UTF-8 without telling you. How would you notice?

<details><summary>Answers</summary>

1. It fails loudly, so you fix it. `latin-1` maps every byte to some character, so wrong letters flow silently into your data.
2. They tell pandas that `,` is the decimal point and that a space separates thousands, so `"1 249,00"` becomes `1249.0`.
3. A dict of every sheet: `{sheet_name: DataFrame}`.
4. Read with a strict, explicit encoding so it fails, and have a validation check on text columns (Week 5). Never use `errors="ignore"`.
</details>

---

<a id="day-26"></a>
## Day 26 · Object storage (S3 with moto) + context managers and atomic writes

⏱ ~55 min · 📁 `src/day26/exercises26.py`, `shopflow/src/shopflow/fileutils.py`

> 🎯 **By the end you can:** list and download files from S3 by prefix, and write files so a crash never leaves a half-written one behind.
> 💼 **At work:** clickstream, partner exports and logs usually arrive in S3, Azure Blob or GCS. The API is nearly identical everywhere.

### 📖 Learn (15 min)
- `cd shopflow; uv add boto3; uv add --dev "moto[s3]"`. **moto** fakes AWS inside your Python process: no AWS account, no cost.
- S3 has **buckets** and **keys**. Folders are just key prefixes: `clickstream/dt=2026-11-01/events-0001.jsonl`.
- `list_objects_v2` returns at most 1000 keys, so always use the paginator: `s3.get_paginator("list_objects_v2").paginate(Bucket=..., Prefix=...)`.
- A **context manager** runs setup and cleanup around a block (`with open(...)`). Write your own with `@contextlib.contextmanager`: code before `yield` is setup, code after is cleanup, and `try/finally` makes cleanup run on errors too.
- **Atomic write:** write to `file.tmp`, close it, then `os.replace(tmp, final)`. Readers see the old file or the new file, never half of one.
- Docs: https://docs.getmoto.org/en/latest/ · https://docs.python.org/3/library/contextlib.html

### 💻 Do (30 min)
- [ ] **1.** Set up fake S3 and seed 3 days of clickstream:
  ```python
  import json, os, boto3
  from moto import mock_aws

  os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
  os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
  with mock_aws():
      s3 = boto3.client("s3", region_name="eu-central-1")
      s3.create_bucket(Bucket="shopflow-clickstream",
                       CreateBucketConfiguration={"LocationConstraint": "eu-central-1"})
      for day in ["2026-11-01", "2026-11-02", "2026-11-03"]:
          events = [{"user_id": u, "event": "view", "product_id": 10 + u, "ts": f"{day}T10:0{u}:00Z"} for u in range(3)]
          body = "\n".join(json.dumps(e) for e in events).encode()
          s3.put_object(Bucket="shopflow-clickstream", Key=f"clickstream/dt={day}/events-0001.jsonl", Body=body)
      # your code here, inside the `with` block
  ```
- [ ] **2.** List every key under `clickstream/` with the paginator. Then list only `dt=2026-11-02`.
- [ ] **3.** Read one object line by line: `s3.get_object(...)["Body"].iter_lines()` yields bytes, so decode and `json.loads` each line.
- [ ] **4.** Write a `@contextmanager` called `timer(label)` that logs how long the block took. Use it around task 2.
- [ ] **5.** In `fileutils.py`, write `atomic_write(path, mode="w", encoding="utf-8")` as a context manager: write to `path.with_name(path.name + ".tmp")`, and after the `with open(...)` block **closes**, call `os.replace`. On an exception, delete the temp file and re-raise.
- [ ] **6.** *Explain why:* raise an exception halfway through writing with `atomic_write`. Check that the old file is untouched and no `.tmp` is left. Why must the file be closed before `os.replace` on Windows?
- ⭐ *Stretch:* move the setup into a pytest fixture in `tests/conftest.py` that yields the S3 client inside `mock_aws()`.

### ✅ Check yourself (5 min)
1. Why use the paginator instead of one `list_objects_v2` call?
2. What does code after `yield` in a `@contextmanager` do, and when does it run?
3. Why is `os.replace` atomic, and what does that protect against?
4. moto vs a real AWS test bucket: trade-offs?

<details><summary>Answers</summary>

1. One call returns at most 1000 keys. Without paginating, you silently miss files once a prefix grows.
2. It's the cleanup. Inside `try/finally` it runs whether the block succeeds or raises.
3. The rename happens in one step on the same filesystem, so readers see the complete old file or the complete new file. It protects against half-written files after a crash or kill.
4. moto is free, fast, offline and safe for CI, but it can differ from real AWS in edge cases (permissions, consistency, newer features). Run a few integration tests against a real sandbox bucket too.
</details>

---

<a id="day-27"></a>
## Day 27 · Concurrency for extraction: threads and rate limits

⏱ ~50 min · 📁 `src/day27/exercises27.py`

> 🎯 **By the end you can:** speed up many slow API calls with a thread pool, without hammering the source.
> 💼 **At work:** fetching 5,000 product details one by one at 300 ms each takes 25 minutes. With 8 threads it takes about 3.

### 📖 Learn (10 min)
- **I/O-bound** work (waiting on network or disk) → threads help, because waiting threads release the GIL. **CPU-bound** work (parsing, maths) → threads don't help in standard Python. Use `ProcessPoolExecutor`, or Spark.
- `from concurrent.futures import ThreadPoolExecutor, as_completed`. `pool.map(f, items)` returns results in input order. `as_completed(futures)` gives them as they finish.
- An exception in a worker is re-raised when you call `future.result()`. Handle it per item.
- More threads = more load on the source. Cap `max_workers` and add a rate limiter.
- `asyncio` (with `httpx.AsyncClient` or `aiohttp`) handles thousands of concurrent requests in one thread. Know it exists; threads are enough here.
- Docs: https://docs.python.org/3/library/concurrent.futures.html

### 💻 Do (35 min)
- [ ] **1.** Get the unique product IDs from the first 5 carts (`/carts?limit=5`, each cart has `products[].id`).
- [ ] **2.** Fetch each product **sequentially** with `/products/{id}?delay=300` and time it with your Day 26 `timer`.
- [ ] **3.** Do the same with `ThreadPoolExecutor(max_workers=5)` and `as_completed`. Compare the times. Use your `@retry` from Day 21 on the fetch function.
- [ ] **4.** Add this rate limiter, and call `limiter.wait()` before each request. Set it to 4 requests per second and time it again.
  ```python
  import threading, time

  class RateLimiter:
      def __init__(self, per_second: float):
          self.interval = 1 / per_second
          self.lock = threading.Lock()
          self.next_time = time.monotonic()

      def wait(self) -> None:
          with self.lock:
              now = time.monotonic()
              sleep_for = self.next_time - now
              self.next_time = max(now, self.next_time) + self.interval
          if sleep_for > 0:
              time.sleep(sleep_for)
  ```
- [ ] **5.** Add one invalid ID (`999999`, which returns 404). Make sure the other products are still collected, and the failure is logged with its ID.
- [ ] **6.** *Explain why:* why does `time.sleep` happen **outside** the `with self.lock:` block?
- ⭐ *Stretch:* run a CPU-heavy function (`sum(i * i for i in range(5_000_000))`) 4 times with threads, then with `ProcessPoolExecutor`. Put the code under `if __name__ == "__main__":`, which Windows needs for processes.

### ✅ Check yourself (5 min)
1. Why do threads speed up API calls but not number crunching?
2. `pool.map` vs `as_completed`: when do you use which?
3. What happens to an exception raised inside a worker thread?
4. The API allows 10 requests per second. Is `max_workers=10` enough to stay under it?

<details><summary>Answers</summary>

1. While a thread waits on the network it releases the GIL, so others run. CPU work holds the GIL, so only one thread computes at a time.
2. `map` when you want results in input order and are fine with one failure stopping the loop. `as_completed` to handle each result, or error, as soon as it's ready.
3. It's stored in the future and re-raised when you call `.result()`. If you never call it, the error is silently lost.
4. No. 10 workers with fast responses can make far more than 10 calls per second. Workers limit *concurrency*, not *rate*. You need a rate limiter.
</details>

---

<a id="day-28"></a>
## Day 28 · 🛠 Build day: one connector interface for every source + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/sources/base.py`, `shopflow/src/shopflow/runner.py`

> 🎯 **By the end you can:** plug any new source into the pipeline by writing one small class.
> 💼 **At work:** a shared interface is what lets a team add source #20 in a day instead of a week.

### 💻 Do (40 min)
- [ ] **1.** In `base.py`, define the interface with `typing.Protocol`:
  ```python
  from typing import Iterator, Protocol

  class Connector(Protocol):
      source: str           # "erp"
      entity: str           # "orders"
      watermark_field: str  # field in each record used for the next watermark
      def extract(self, since: str | None) -> Iterator[dict]: ...
  ```
- [ ] **2.** Write three classes that match it (no inheritance needed): `ErpOrders` (Day 24, `updated_at`), `SupplierPrices` (Day 25, reads files with `dtype=str` and adds `_source_file` and `_file_date` from the filename) and `S3Clickstream` (Day 26, takes a boto3 client and adds `_object_key`).
- [ ] **3.** In `raw.py`, add `write_raw_records(records, *, base_dir, source, entity, load_date, meta) -> int`. It streams records to `part-0001.jsonl` with your `atomic_write`, writes `_metadata.json`, and returns the row count.
- [ ] **4.** In `runner.py`: `run(connector, *, base_dir, load_date, state_dir)`. Load the watermark, extract, write raw, track the max `watermark_field`, and save the new watermark **only after** the write succeeds. Log one summary line.
- [ ] **5.** Tests: a `FakeConnector` that yields 3 records proves the runner writes 3 rows and saves the watermark; a connector that raises halfway proves the watermark is **not** saved; `ErpOrders` against a tiny SQLite DB in `tmp_path`; `S3Clickstream` with moto.
- [ ] **6.** 📘 Update **§2 Extract** and **§3 Raw layer** in your [playbook](new-source-playbook.md#3--raw-layer) (atomic writes, watermark after write, one interface).

### ✅ Weekly quiz
1. What's a watermark, and what happens if you save it too early?
2. Why read supplier files with `dtype=str` in the raw step?
3. Explain out loud, as in an interview: "How would you extract a large, changing table from a production database?"
4. Threads or processes for downloading 2,000 S3 files? Why?
5. `Protocol` vs an abstract base class: what's the difference?

<details><summary>Answers</summary>

1. The highest change marker you've safely loaded (like the max `updated_at`). The next run asks only for rows after it. Saving it before the data is written means a crash loses those rows forever.
2. Raw should keep values as received. Converting `"1 249,00"` too early can lose or corrupt information, and conversion rules belong in staging, where they're tested and validated.
3. Incremental extraction on an indexed `updated_at` (or CDC for deletes), with parameterised queries, streaming with `fetchmany`, a read replica so production isn't slowed down, and a watermark saved only after a successful atomic write. Add a lookback or `>=` with downstream dedupe for same-timestamp rows, plus a full-reload option for backfills.
4. Threads. Downloading is I/O-bound, so threads overlap the waiting. Cap the workers to respect limits.
5. A `Protocol` is structural: any class with the right attributes and methods matches, no inheritance needed, and it's checked by type checkers. An ABC is nominal: classes must inherit from it, and Python stops you creating one that's missing an abstract method.
</details>

---

## 🏁 End of week 4: I can…
- [ ] Extract incrementally from a database with parameterised SQL and a watermark
- [ ] Read `;` CSVs, decimal commas, cp1250 files and multi-sheet Excel correctly
- [ ] List and read S3 objects by prefix, and test it with moto
- [ ] Write my own context manager and write files atomically
- [ ] Speed up I/O-bound extraction with a thread pool and a rate limiter
- [ ] Plug different sources into one connector interface and runner

📈 Rate your confidence for Week 4 in the [progress tracker](README.md#-progress-tracker).

# Week 9 — Concurrency and performance

"How would you make this faster?" is a guaranteed senior interview question. The answer always starts with **"it depends whether it's I/O-bound or CPU-bound."**

---

## Day 49 — Concurrency concepts 🧠

**Learn (15 min)**
- **I/O-bound:** waiting on the network, disk or a database (API extraction). **CPU-bound:** computation (parsing, hashing, maths).
- The **GIL** (Global Interpreter Lock) means only one thread runs Python bytecode at a time in standard CPython. Threads still help with I/O, because waiting releases the GIL.
- **Threads** (`ThreadPoolExecutor`): I/O-bound work, shared memory.
- **Processes** (`ProcessPoolExecutor`): CPU-bound work, real parallelism, but data has to be copied between processes.
- **asyncio:** one thread, many tasks taking turns at `await` points. Great for thousands of concurrent I/O calls.
- Note: free-threaded ("no-GIL") Python builds exist since 3.13. Interviewers may ask about them, and they're still being adopted.

**Do (30 min)** in `src/day49/exercises49.py`
1. `fake_io(i)`: `time.sleep(0.5)`. Run 10 calls (a) sequentially, (b) with `ThreadPoolExecutor(max_workers=10)`. Time both.
2. `cpu_work(n)`: `sum(i * i for i in range(n))` with n = 5,000,000. Run 4 of them (a) sequentially, (b) with threads, (c) with `ProcessPoolExecutor`. Time all three. Explain the results.
   (On Windows, process pools need the `if __name__ == "__main__":` guard. That's another reason it exists.)

**Check yourself**
1. Why did threads speed up `fake_io` but not `cpu_work`?
2. Why do processes help CPU-bound work, and what's the cost?
3. When is asyncio better than threads?
4. Why does `ProcessPoolExecutor` on Windows need the `__main__` guard?

<details><summary>Answers</summary>

1. Sleeping or waiting releases the GIL, so threads overlap their waiting. CPU work holds the GIL, so threads take turns: no speedup, sometimes a slowdown.
2. Each process has its own interpreter and GIL, so you get true parallelism. The cost is start-up time, memory, and pickling data between processes.
3. Very high concurrency (hundreds or thousands of connections) with low overhead per task, when async libraries are available.
4. Windows *spawns* new processes that re-import your module. Without the guard, each child would start the pool again, endlessly.
</details>

---

## Day 50 — 🛠 Concurrent extraction with threads

**Do (40 min)** in `extract.py`
1. Fetch page 1 to learn `total`, then compute all the `skip` values.
2. Fetch the remaining pages with `ThreadPoolExecutor(max_workers=settings.max_workers)` and `as_completed`. Keep your `@retry` on `fetch_page`.
3. If a future raises, log it and fail the run. Don't silently drop pages.
4. Sort the records by id (completion order is random) before saving, so the output is deterministic.
5. Compare the extraction time with the sequential version. Add `SHOPFLOW_MAX_WORKERS` to the settings.

**Check yourself**
1. Why compute all the page offsets up front?
2. Why sort after concurrent fetching?
3. What's the risk of `max_workers=100` against someone else's API?
4. How do exceptions inside threads reach your main code?

<details><summary>Answers</summary>

1. Pages become independent tasks, so they can run in parallel. The sequential loop only knows the next offset after the previous call.
2. Results finish in random order. A deterministic output means idempotent files and easy diffs.
3. Rate limiting (429s), getting your IP blocked, or overloading their service. Be a polite client.
4. They're stored in the `Future`. Calling `future.result()` re-raises them in the main thread.
</details>

---

## Day 51 — asyncio 🧠

**Learn (15 min)**
- `async def` defines a coroutine. `await` pauses it until the result is ready, letting others run. `asyncio.run(main())` starts the event loop.
- `asyncio.gather(*coros)` runs many concurrently. `asyncio.Semaphore(n)` caps how many run at once.
- `httpx.AsyncClient` is an async HTTP client.
- **Never call blocking code** (`time.sleep`, `requests.get`) inside async code. It freezes everything.

**Do (35 min)** in `src/day51/exercises51.py`
1. `async def fake_io(i): await asyncio.sleep(0.5)`. Gather 100 of them. How long does it take?
2. Replace `asyncio.sleep` with `time.sleep` and run it again. Explain what you see.
3. `uv add httpx`. Fetch all the DummyJSON product pages concurrently with an `AsyncClient` and a `Semaphore(5)`.
4. Compare it with your threads version. Which would you keep in `shopflow`, and why? (Write 3 sentences.)

**Check yourself**
1. What does `await` do?
2. Why did `time.sleep` destroy concurrency?
3. What's a semaphore for here?
4. Threads vs asyncio for a pipeline calling 20 pages: which would you choose?

<details><summary>Answers</summary>

1. It suspends the current coroutine until the awaited thing finishes, handing control back to the event loop.
2. It blocks the single event-loop thread, so nothing else can run. The tasks run one after another.
3. It limits how many requests are in flight at once (being polite to the API, respecting rate limits).
4. Either is fine. Threads are simpler and work with `requests` and your existing decorator. asyncio pays off at a much higher scale. Simplicity is a valid senior answer.
</details>

---

## Day 52 — Profiling and optimisation 🧠

**Learn (10 min)**
- **Measure before you optimise.** `cProfile` shows where the time goes. `tracemalloc` shows where the memory goes.
- `python -m cProfile -s cumtime script.py`, or `pstats` in code.

**Do (40 min)** in `src/day52/exercises52.py`
1. Profile this deliberately slow code with 20k products and 200k cart items:
   ```python
   def enrich_items(items, products):
       result = []
       for item in items:
           for p in products:                       # what's the complexity?
               if p["id"] == item["product_id"]:
                   result = result + [{**item, "category": p["category"]}]   # and this?
       return result
   ```
2. Find the 2 bottlenecks in the profiler output. Fix them (a dict lookup, `append`). Measure again.
3. Profile your full `shopflow run`. Where does the time go: network, validation, or DB? Write the answer in the README.

**Check yourself**
1. Name the two problems in `enrich_items` and their complexity.
2. Why measure before optimising?
3. `cumtime` vs `tottime` in cProfile?
4. Your pipeline is slow because 90% of the time is spent waiting for the API. What would you do?

<details><summary>Answers</summary>

1. The nested loop makes it O(n·m) → build `{id: product}` once for O(1) lookups. `result = result + [...]` copies the list every iteration, which is O(n²) → use `append`.
2. Intuition is often wrong. You'd risk optimising code that isn't the bottleneck.
3. `tottime` is time spent in the function itself. `cumtime` also includes the functions it calls.
4. Concurrency (threads or async), incremental fetching (less data), caching. Optimising the Python code won't help.
</details>

---

## Day 53 — Week 9 review 🔁

**Weekly quiz** (try to answer out loud, as in an interview)
1. "Our nightly job takes 4 hours. How would you speed it up?" Give a structured answer.
2. Explain the GIL to a non-Python engineer in 3 sentences.
3. Threads, processes, asyncio: one use case each in data engineering.
4. What does "deterministic output" mean, and why does concurrency threaten it?
5. Name 2 ways to reduce memory usage when processing a 20GB file in Python.

<details><summary>Answers</summary>

1. Measure first (which step, and is it I/O or CPU?) → I/O: concurrency, incremental loads, pushing work to the database. CPU: vectorize, polars, multiprocessing, a better algorithm, or a distributed engine (Spark). Also: skip unnecessary work, and use partitioning or pruning.
2. CPython has a lock so only one thread executes Python code at a time. Waiting on I/O releases it, so threads help network-heavy work. For heavy computation you need multiple processes (or native libraries that release the lock).
3. Threads: parallel API calls. Processes: CPU-heavy parsing or transforms of many files. asyncio: thousands of concurrent requests or streams.
4. The same input always gives byte-identical output. Concurrent completion order is random, so you need explicit sorting.
5. Stream with generators or chunks (`chunksize`, polars streaming / `scan_*`). Read only the needed columns and use compact dtypes, or let DuckDB/polars query it out-of-core.
</details>

📝 Confidence log.

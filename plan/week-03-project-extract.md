# Week 3 — 🛠 Project kickoff: `shopflow` (Extract)

## The project

**`shopflow`** is an e-commerce data pipeline that will grow over the coming weeks:

```
DummyJSON API ──► raw (JSON) ──► validated staging ──► DuckDB warehouse ──► marts ──► reports / AI assistant
   extract          bronze           silver              load               gold
                                         ▲
                              LLM enrichment + data-quality checks
```

- **Source:** https://dummyjson.com, a free fake e-commerce API with `/products`, `/carts` and `/users`. It supports `?limit=&skip=` pagination.
- **Why this project:** it covers what senior data engineering interviews ask about (APIs, pagination, retries, idempotency, validation, modelling, SQL, testing, orchestration, CI, AI), and it's in the e-commerce domain you know.
- **Separate public GitHub repo:** this is what you'll link in your CV.

It doesn't need to be impressive. It needs to be **clean, tested, and explainable**. A small project you can defend in an interview is worth more than a big one you can't.

---

## Day 19 — Design + repo setup 🛠

**Learn (15 min)**
- **ETL vs ELT:** transform before loading vs load raw data first and transform inside the warehouse. Modern stacks are mostly ELT.
- **Layers:** *raw/bronze* (exactly what the source sent) → *staging/silver* (validated, typed, cleaned) → *marts/gold* (business tables).
- **Idempotency:** running the pipeline twice for the same input gives the same result. No duplicates, no drift.

**Do (35 min)**
1. Create the project **outside** this repo:
   ```
   uv init --package shopflow
   cd shopflow
   uv add requests
   uv add --dev pytest ruff
   ```
2. Create this structure (empty files are fine):
   ```
   shopflow/
     src/shopflow/__init__.py
     src/shopflow/extract.py
     src/shopflow/validate.py
     src/shopflow/load.py
     src/shopflow/transform.py
     tests/
     sql/
     data/          ← add to .gitignore
     README.md
   ```
3. Write the README: **Goal**, **Architecture** (the diagram above), **Data sources**, **Layers**, and a **Roadmap** checklist of the coming weeks.
4. `git init`, first commit, create a public GitHub repo, push.

**Check yourself**
1. ETL vs ELT: what's the difference, and why is ELT common now?
2. Why keep the raw layer untouched?
3. Define an idempotent pipeline in one sentence.
4. Why is `data/` in `.gitignore`?

<details><summary>Answers</summary>

1. ETL transforms before loading. ELT loads raw data and transforms it inside the warehouse. Cheap storage and powerful warehouses (Snowflake, BigQuery, DuckDB) made ELT practical, and it keeps raw data available for reprocessing.
2. You can **reprocess** when logic changes or bugs are found, and you can **audit** what the source actually sent.
3. Running it N times with the same input produces the same output as running it once.
4. Data is large, changes often, and may be sensitive. Git is for code. Data belongs in storage.
</details>

---

## Day 20 — HTTP and APIs 🧠🛠

**Learn (10 min)**
- HTTP: `GET` reads data. Query params look like `?limit=30&skip=0`.
- Status codes: `200` OK · `400` bad request · `401/403` auth · `404` not found · `429` too many requests · `5xx` server error.
- **Always set a timeout.** `requests` waits forever by default.
- Try it in your browser: https://dummyjson.com/products?limit=5&skip=0

**Do (35 min)** in `src/shopflow/extract.py`
1. `BASE_URL = "https://dummyjson.com"`
2. `fetch_page(entity: str, limit: int, skip: int) -> dict` using `requests.get(url, params=..., timeout=10)` and `response.raise_for_status()`.
3. Call it for products and print `total`, `skip`, `limit` and the keys of the first product.
4. Test it **without the network**: `uv add --dev responses` and register a fake response for the URL. Assert that your function returns the parsed JSON. Docs: https://github.com/getsentry/responses

**Check yourself**
1. Why always pass a `timeout`?
2. Which failures are worth retrying, and which aren't?
3. What does `raise_for_status()` do?
4. Why mock HTTP in unit tests?

<details><summary>Answers</summary>

1. Without one, a stuck connection hangs your pipeline forever, and a scheduler slot or worker is wasted.
2. Retry: `429`, `500/502/503/504`, connection errors and timeouts (they're temporary). Don't retry: `400`, `401`, `403`, `404` (they'll fail the same way again).
3. Raises `HTTPError` if the status is 4xx or 5xx.
4. Tests become fast, deterministic and offline, and you can simulate errors that are hard to trigger for real.
</details>

---

## Day 21 — Pagination and the raw layer 🛠

**Learn (10 min)**
- **Offset pagination** (`skip`/`limit`) vs **cursor pagination** (`next_token`). Offset can skip or duplicate rows if data changes while you're paging.
- **Hive-style partitioning:** `data/raw/products/dt=2026-10-21/products.json`

**Do (35 min)**
1. `fetch_all(entity, page_size=50) -> list[dict]`: loop over `skip = 0, 50, 100…` until `skip >= total`. Each entity's records live under a key with the same name (`response["products"]`). (Don't use `limit=0`, because the point is to practise pagination.)
2. `save_raw(entity, records, run_date)` writes to `data/raw/{entity}/dt={run_date}/{entity}.json`. Rerunning on the same day **overwrites**, which is idempotent.
3. `main()` extracts products, carts and users, and logs how many records each one returned.
4. Test pagination with a fake API that returns 3 pages (`total=120`, `page_size=50`). Assert you get 120 records and exactly 3 requests.

**Check yourself**
1. What can go wrong with offset pagination while the source is changing?
2. Why partition raw data by date?
3. Why does overwriting the same path make reruns idempotent? What would appending timestamped files do?
4. What metadata is worth saving next to raw data?

<details><summary>Answers</summary>

1. Inserts or deletes shift the offsets, so you can **skip** rows or get **duplicates**. Cursor or keyset pagination avoids this.
2. You can reprocess or backfill a single day, delete old data easily, and query engines can skip partitions you don't need (partition pruning).
3. Same input → same file. Appending creates duplicates on every rerun unless the downstream steps dedupe.
4. `extracted_at`, source URL and params, row count, run ID, pipeline version. These help with lineage and debugging.
</details>

---

## Day 22 — Retries, backoff, logging 🛠

**Learn (10 min)**
- **Exponential backoff:** wait 1s, 2s, 4s… between attempts. **Jitter:** add randomness so many clients don't retry at the same moment.
- Only retry **retryable** errors (see Day 20).

**Do (35 min)**
1. `fetch_page_with_retry(...)`: max 3 attempts, `sleep(2 ** attempt + random.uniform(0, 1))`, retrying only on connection errors, timeouts, 429 and 5xx. Log every attempt at WARNING.
2. Test 1: the fake API returns `503, 503, 200` → success after 3 calls.
3. Test 2: the fake API returns `404` → raises immediately after **1** call.
4. Use `monkeypatch.setattr("time.sleep", lambda s: None)` so tests don't actually wait. (Patch where `sleep` is *used*. If you did `from time import sleep`, patch `shopflow.extract.sleep`.)
5. Note: the `tenacity` library does all this in production code. You're writing it yourself to understand it.

**Check yourself**
1. Why exponential backoff *and* jitter?
2. Why not retry a 400?
3. Why patch `sleep` in tests?
4. What's dangerous about retrying a non-idempotent request (like "create order")?

<details><summary>Answers</summary>

1. Backoff gives an overloaded service time to recover. Jitter stops a "thundering herd" of clients retrying in sync.
2. It's a client error. The same request will fail the same way.
3. Tests stay fast (milliseconds instead of seconds), and the slow part isn't the behaviour you're testing anyway.
4. If the first request actually succeeded but the response was lost, the retry creates a **duplicate**. That's why APIs use idempotency keys.
</details>

---

## Day 23 — Week 3 review 🔁

**Do (30–40 min)**
1. Run `ruff check`, `ruff format` and `pytest`. Everything should be green.
2. README: add **How to run** (`uv run python -m shopflow.extract`) and **What I learned**.
3. Look at your git log. Are the messages clear? (Use the imperative mood: "Add pagination to extract".)
4. Write 3 "I can now…" sentences in your confidence log.

**Weekly quiz**
1. Walk through what your extract does, start to finish, in 60 seconds (out loud). This is interview practice.
2. If DummyJSON goes down for 10 minutes during your run, what happens?
3. If you run the extract twice today, what's on disk?
4. Where would you add a check that "today's product count is suspiciously low"?
5. What would change if the API used cursor pagination?

<details><summary>Answers</summary>

1. (Your own words.) Paginate through each entity, retry temporary failures with backoff, save raw JSON partitioned by date, and log counts.
2. Retries are exhausted after about 7 seconds and the run fails with a logged error. Then the scheduler (Week 8) retries the whole task later.
3. The same files, overwritten. That's idempotent.
4. After extract: compare the count with the previous run or a threshold, and warn or fail. Full data-quality checks come in Week 7.
5. The loop would follow `next_cursor` until it's empty, instead of computing `skip`. It's more stable when data changes during extraction.
</details>

📝 Confidence log.

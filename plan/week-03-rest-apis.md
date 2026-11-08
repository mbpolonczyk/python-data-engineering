# Week 3 · Source #1: REST APIs

**Phase 2 — Integrating new data sources** · Days 19–23
[← Week 2](week-02-files-packages-tests.md) · [Plan overview](README.md) · [Week 4 →](week-04-more-sources.md)

> **This week's outcome:** you can pull every record from a paginated, authenticated REST API, survive flaky networks with retries, and stream the data instead of holding it all in memory.
>
> **Project milestone:** `shopflow` gets `raw.py` (the raw layer writer) and a DummyJSON connector for products, users and carts, with tests that never call the real API.

| Day | Topic | Time |
|---|---|---|
| 19 | HTTP basics with `requests` | ~45 min |
| 20 | Pagination + the raw layer writer | ~55 min |
| 21 | Auth, rate limits and a `@retry` decorator | ~60 min |
| 22 | Generators and `itertools` for streaming | ~45 min |
| 23 | 🛠 Build day: DummyJSON connector end to end + quiz | ~60 min |

We use https://dummyjson.com: a free fake shop API. No account needed. Be polite: small page sizes, no tight loops.

---

<a id="day-19"></a>
## Day 19 · HTTP basics with `requests`

⏱ ~45 min · 📁 `src/day19/exercises19.py`

> 🎯 **By the end you can:** call an API with query params, headers and a timeout, and react correctly to each kind of status code.
> 💼 **At work:** "can you pull data from their API?" is the most common new-source request. Reading the docs well saves days.

### 📖 Learn (15 min)
- `GET` reads data. Query params: `requests.get(url, params={"limit": 5, "skip": 0}, timeout=10)`.
- **Always set a `timeout`.** Without one, `requests` can wait forever and your job hangs.
- Status codes: `2xx` OK · `400` bad request · `401/403` auth problem · `404` not found · `429` too many requests · `5xx` server problem.
- `resp.raise_for_status()` raises `HTTPError` for 4xx/5xx. `resp.json()` parses the body. `resp.headers` is a case-insensitive dict.
- Use a `requests.Session()` to reuse connections and set shared headers once.
- Docs: https://requests.readthedocs.io/en/latest/user/quickstart/ · https://dummyjson.com/docs

### 💻 Do (25 min)
- [ ] **1.** `cd shopflow; uv add requests`. In your exercise file, use the shopflow environment: `uv run --project shopflow python src/day19/exercises19.py` from the repo root.
- [ ] **2.** Fetch `https://dummyjson.com/products` with `params={"limit": 5, "skip": 0, "select": "title,price,category"}`. Print `total`, `skip`, `limit` and the first product. What are the top-level keys?
- [ ] **3.** Call `https://dummyjson.com/http/404` and `https://dummyjson.com/http/503`. Print `status_code`, then call `raise_for_status()` inside `try/except requests.HTTPError` and log the error.
- [ ] **4.** Call `https://dummyjson.com/products?delay=3000` with `timeout=1`. Which exception do you get? Catch exactly that one.
- [ ] **5.** Print `resp.headers`. Is there anything about rate limits or caching? Write down what you find.
- [ ] **6.** 📘 Fill in **§1 Discovery** in your [playbook](new-source-playbook.md#1--discovery-before-writing-any-code) for DummyJSON: kind, auth, format, volume (`total`), how to get new data, limits.
- ⭐ *Stretch:* try `limit=0`. What does DummyJSON return? Why would you still avoid "give me everything" on a real API?

### ✅ Check yourself (5 min)
1. What's the difference between a 401 and a 403?
2. Which status codes are worth retrying, and which aren't?
3. Why is a missing `timeout` a production incident waiting to happen?
4. `resp.json()` works but `"products"` is missing. What should your code do?

<details><summary>Answers</summary>

1. 401: we don't know who you are (missing or bad credentials). 403: we know who you are, but you're not allowed.
2. Retry: timeouts, connection errors, 429 and 5xx, because they're often temporary. Don't retry other 4xx (400, 401, 403, 404): the same request will fail the same way.
3. A hung connection blocks the job forever. Nothing fails, so nothing alerts, and the data is just late.
4. Fail loudly with a clear error (the API contract changed). Don't silently treat it as "0 products".
</details>

---

<a id="day-20"></a>
## Day 20 · Pagination + the raw layer writer

⏱ ~55 min · 📁 `shopflow/src/shopflow/sources/dummyjson.py`, `shopflow/src/shopflow/raw.py`

> 🎯 **By the end you can:** fetch every page of an API without off-by-one bugs, and save each page as received in a dated raw partition.
> 💼 **At work:** "we only got the first 30 rows" is the classic pagination bug, and it can go unnoticed for months.

### 📖 Learn (10 min)
- **Offset pagination** (DummyJSON): `limit` = page size, `skip` = how many to skip. Stop when `skip >= total` or a page comes back empty.
- Other styles you'll meet: page numbers (`?page=3`), and **cursors** (`next_cursor` or a `next` URL in the response). Cursors are safer when data changes during extraction.
- Raw layer rules: save **exactly** what you received, partition by load date, save metadata, and make a rerun **replace** the partition rather than add to it.

### 💻 Do (35 min)
- [ ] **1.** In `dummyjson.py`: `fetch_page(session, entity, *, limit, skip) -> dict`, with a timeout and `raise_for_status()`.
- [ ] **2.** `fetch_all_pages(session, entity, *, page_size=50) -> list[dict]`: loop with `skip` until done. Each list item is one **whole page** (the response dict).
- [ ] **3.** In `raw.py`: `write_raw_pages(pages, *, base_dir, source, entity, load_date, request_info) -> Path`. It:
  - deletes the partition folder if it exists (`shutil.rmtree`), then recreates it,
  - writes `part-0001.json`, `part-0002.json`, … with `json.dump(page, f, ensure_ascii=False)`,
  - writes `_metadata.json` with `source`, `entity`, `load_date`, `extracted_at` (UTC), `request_info`, `pages`, `row_count`.
- [ ] **4.** Run it for `products` with `page_size=50`. Check that `row_count == total` (194 at the time of writing).
- [ ] **5.** *Bug hunt:* this loop has two bugs. Find them before running it.
  ```python
  skip, pages = 0, []
  while True:
      page = fetch_page(s, "products", limit=50, skip=skip)
      skip += 1
      if skip > page["total"]:
          break
      pages.append(page)
  ```
- [ ] **6.** 📘 Fill in **§3 Raw layer** in your [playbook](new-source-playbook.md#3--raw-layer): your folder pattern and metadata fields.
- ⭐ *Stretch:* what happens if a product is deleted while you're on page 2? Write one sentence on why cursors avoid it.

### ✅ Check yourself (5 min)
1. Name two ways to know you've reached the last page.
2. Why does the raw writer delete the partition before writing?
3. Why keep the pages as received instead of flattening products into one list first?
4. Offset pagination over a table that's changing: what can go wrong?

<details><summary>Answers</summary>

1. `skip + len(items) >= total`, or an empty page. Robust code checks both, so a wrong `total` can't cause an endless loop.
2. Idempotency. A rerun for the same date replaces the data instead of leaving old and new parts mixed together.
3. Raw must be a faithful copy. Flattening is a transformation, and it can lose fields like `total` that you may need for checks later.
4. Rows inserted or deleted between page calls shift the offsets, so you skip or duplicate records. Dedupe downstream, or use cursor or `updated_at`-based extraction.
</details>

---

<a id="day-21"></a>
## Day 21 · Auth, rate limits and a `@retry` decorator

⏱ ~60 min · 📁 `shopflow/src/shopflow/http_client.py`, `src/day21/exercises21.py`

> 🎯 **By the end you can:** log in to an API without putting secrets in code, and retry temporary failures with exponential backoff, using your own decorator.
> 💼 **At work:** APIs fail every day. A pipeline that retries the right errors, the right way, is the difference between "self-healed" and "paged at 3 a.m.".

### 📖 Learn (15 min)
- **Bearer tokens:** log in once, then send `Authorization: Bearer <token>` with every request. DummyJSON: `POST /auth/login` with JSON `{"username": ..., "password": ...}` returns `accessToken`. Test user: `emilys` / `emilyspass` (see https://dummyjson.com/docs/auth).
- **Secrets come from the environment**, never from code or git: `os.environ["DUMMYJSON_PASSWORD"]`. In PowerShell: `$env:DUMMYJSON_PASSWORD = "emilyspass"`.
- **Decorators:** a function that takes a function and returns a wrapped one. `@retry(...)` above `def f` means `f = retry(...)(f)`. Use `@functools.wraps(func)` so the wrapper keeps the original name and docstring.
- **Exponential backoff with jitter:** wait `base * 2**attempt` seconds, randomized: `random.uniform(0, base * 2**attempt)`. Jitter stops 100 clients retrying at the same moment. If a 429 has a `Retry-After` header, respect it.
- Docs: https://docs.python.org/3/library/functools.html#functools.wraps

### 💻 Do (35 min)
- [ ] **1.** Warm-up in `exercises21.py`: write a `@timed` decorator that logs how long a function took. Apply it to a function with `time.sleep(0.3)`. Print `f.__name__` with and without `functools.wraps`.
- [ ] **2.** In `http_client.py`, write `retry(max_attempts=4, base_delay=0.5)`, a decorator factory (3 levels of functions). It retries on `requests.Timeout`, `requests.ConnectionError`, and `requests.HTTPError` **only** when the status is 429 or ≥ 500. Log a WARNING on each retry, and re-raise after the last attempt.
- [ ] **3.** Test it by hand: decorate a function that calls `https://dummyjson.com/http/503` and watch the retries in the log. Then call `/http/404`: it must fail **immediately**.
- [ ] **4.** `login(session) -> None`: read `DUMMYJSON_USER` and `DUMMYJSON_PASSWORD` from env, call `/auth/login`, set `session.headers["Authorization"] = f"Bearer {token}"`. Verify with `GET /auth/me`. Never log the token.
- [ ] **5.** Add `.env` to `shopflow/.gitignore` now, before you need it.
- ⭐ *Stretch:* make `retry` respect a `Retry-After` header (seconds) on 429 responses.

<details><summary>Hint for task 2 (only after you've tried)</summary>

`def retry(max_attempts, base_delay):` → `def decorator(func):` → `@functools.wraps(func) def wrapper(*args, **kwargs):` with a `for attempt in range(max_attempts):` loop and `try/except`. Write a small `is_retryable(exc) -> bool` helper first. For `HTTPError`, the status is in `exc.response.status_code`.
</details>

### ✅ Check yourself (5 min)
1. Why does `@functools.wraps` matter?
2. Why add jitter to the backoff?
3. Why must a retried request be safe to repeat? Which HTTP methods are usually safe?
4. The password is in the code "just for now" and gets pushed. What do you do?

<details><summary>Answers</summary>

1. Without it, the wrapper replaces the function's `__name__` and docstring, so logs, tracebacks and tools show `wrapper` instead of the real name.
2. Without it, many clients that failed together retry together, and overload the server again (a "thundering herd").
3. A retry may repeat a request that actually succeeded. `GET` is safe and idempotent. `POST` (like creating an order) may create duplicates unless the API supports idempotency keys.
4. Treat it as leaked: rotate the secret immediately. Removing it from git history isn't enough, because it may already have been copied.
</details>

---

<a id="day-22"></a>
## Day 22 · Generators and `itertools` for streaming

⏱ ~45 min · 📁 `src/day22/exercises22.py`, then `dummyjson.py`

> 🎯 **By the end you can:** stream records page by page with generators, so memory stays flat whatever the data size.
> 💼 **At work:** a connector that loads 50 million rows into a list crashes the worker. A generator never holds more than one page.

### 📖 Learn (10 min)
- A function with `yield` returns a **generator**: it runs lazily, one item at a time, and is used up after one pass.
- `yield from other_iterable` hands over every item of another iterable.
- Generator expression: `(o["value"] for o in orders)`, with round brackets and no list.
- `itertools.islice(it, 10)` takes the first 10. `itertools.batched(it, 100)` (Python 3.12+) groups into tuples of 100. `itertools.chain(a, b)` joins iterables.
- Docs: https://docs.python.org/3/library/itertools.html

### 💻 Do (30 min)
- [ ] **1.** Compare `sys.getsizeof([i for i in range(1_000_000)])` with `sys.getsizeof(i for i in range(1_000_000))`. Explain the difference.
- [ ] **2.** *Predict the output*, then run it:
  ```python
  gen = (x * 2 for x in range(3))
  print(list(gen))
  print(list(gen))
  ```
- [ ] **3.** Write `read_jsonl(path)` that **yields** one dict per line from your Day 14 JSONL file. Chain it: `valid = (o for o in read_jsonl(p) if float(o["value"]) > 0)`, then `sum(...)`.
- [ ] **4.** In `dummyjson.py`, change `fetch_all_pages` into `iter_pages(...)`, a generator that yields one page at a time. Add `iter_records(session, entity)` that does `yield from page[entity]` for each page.
- [ ] **5.** Use `itertools.islice(iter_records(s, "products"), 7)`. Watch the log: how many pages were requested? Why?
- [ ] **6.** Use `itertools.batched(iter_records(s, "users"), 25)` and print the size of each batch.
- ⭐ *Stretch:* change `write_raw_pages` so it accepts any iterable of pages and writes each as it arrives, counting rows as it goes.

### ✅ Check yourself (5 min)
1. What does the second `print` in task 2 show, and why?
2. When is a list better than a generator?
3. Why did `islice(..., 7)` only trigger one API call?
4. Generators are lazy. How can that surprise you with errors or open files?

<details><summary>Answers</summary>

1. `[]`. The generator was used up by the first `list()`, and generators don't restart.
2. When you need the data more than once, need `len()` or indexing, or need to sort it, and it fits in memory.
3. The generator only fetches the next page when more items are requested. 7 items fit in the first page.
4. Nothing runs until you iterate, so errors appear later and somewhere else. And a generator reading a file inside `with` keeps it open until it's used up or closed.
</details>

---

<a id="day-23"></a>
## Day 23 · 🛠 Build day: DummyJSON connector end to end + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/sources/dummyjson.py`, `shopflow/tests/test_dummyjson.py`

> 🎯 **By the end you can:** ship an API connector with auth, pagination, retries, streaming and offline tests.
> 💼 **At work:** this is the shape of every API integration you'll build. Tests that hit the live API are flaky, slow and may cost money, so we mock HTTP.

### 💻 Do (40 min)
- [ ] **1.** Write `extract_entity(entity, *, base_dir, load_date, page_size=50) -> Path`. It creates a session, logs in, streams `iter_pages` through your `@retry`-wrapped `fetch_page`, and writes to raw with `write_raw_pages`. Run it for `products`, `users` and `carts`.
- [ ] **2.** Add a `main()` that loops over the three entities and logs one summary line each (`entity, pages, rows, seconds`).
- [ ] **3.** `uv add --dev responses`. In `tests/test_dummyjson.py`, mock a 2-page API and assert that both pages are fetched and all rows are returned:
  ```python
  import responses
  from responses import matchers

  @responses.activate
  def test_iter_records_reads_all_pages():
      url = "https://dummyjson.com/products"
      responses.get(url, json={"products": [{"id": 1}, {"id": 2}], "total": 3, "skip": 0, "limit": 2},
                    match=[matchers.query_param_matcher({"limit": "2", "skip": "0"})])
      responses.get(url, json={"products": [{"id": 3}], "total": 3, "skip": 2, "limit": 2},
                    match=[matchers.query_param_matcher({"limit": "2", "skip": "2"})])
      ...
  ```
- [ ] **4.** More tests: a 503 then a 200 succeeds after one retry; a 404 raises immediately (`len(responses.calls) == 1`); `write_raw_pages` with `tmp_path` writes the right number of parts and `row_count`. Set `base_delay=0` in tests so they're instant.
- [ ] **5.** Run `uv run pytest -v` with Wi-Fi off. Everything should pass.
- [ ] **6.** 📘 Update **§1 Discovery** and **§2 Extract** in your [playbook](new-source-playbook.md#2--extract) with what you learned this week.

### ✅ Weekly quiz
1. Which errors does your `@retry` retry, and why not the others?
2. How does your connector know it has reached the last page?
3. Explain out loud, as in an interview: "Walk me through how you'd integrate a new REST API."
4. Why is the raw partition deleted before writing, and what property does that give the pipeline?
5. Why do tests mock HTTP instead of calling DummyJSON?

<details><summary>Answers</summary>

1. Timeouts, connection errors, 429 and 5xx: they're often temporary. Other 4xx errors mean the request itself is wrong, so retrying wastes time and can hide bugs.
2. It stops when `skip + len(items) >= total` or a page is empty.
3. Read the docs (auth, pagination, limits, incremental options) and fill in a discovery checklist. Store secrets in env vars. Build a session with timeouts, retries with backoff and jitter for retryable errors only, and stream pages with a generator. Land pages as received in a dated raw partition with metadata. Test offline with mocked responses, including the last page and the failures. Then validate downstream.
4. So reruns replace rather than duplicate data. That's idempotency: running it twice gives the same result as running it once.
5. Live calls are slow and flaky, may be rate limited or cost money, and need network and secrets in CI. Mocks are fast and repeatable, and they can simulate failures on demand.
</details>

---

## 🏁 End of week 3: I can…
- [ ] Call a REST API with params, headers and a timeout, and handle each class of status code
- [ ] Paginate to the last page and prove it with a test
- [ ] Authenticate with a token taken from an env var
- [ ] Write a retry decorator with exponential backoff and jitter
- [ ] Stream records with generators and `itertools`
- [ ] Test an API connector with mocked HTTP

📈 Rate your confidence for Week 3 in the [progress tracker](README.md#-progress-tracker).

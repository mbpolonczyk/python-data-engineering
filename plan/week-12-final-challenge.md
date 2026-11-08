# Week 12 · Final challenge: integrate a new source on your own

**Phase 5 — Production & proof** · Days 64–68
[← Week 11](week-11-production.md) · [Plan overview](README.md)

> **This week's outcome:** you integrate a source you've never seen, end to end, using only your [playbook](new-source-playbook.md). When it works, you'll know you can do this at work.
>
> **Project milestone:** `shopflow` has a new source, NBP exchange rates, and a mart with `revenue_pln` for every order. It runs from the CLI, in Docker, with tests and DQ checks.

**The source:** the [National Bank of Poland API](https://api.nbp.pl/en.html). It's free and needs no auth. You'll use **table A** (average rates).
**The business goal:** convert every `shopflow` order to PLN using the rate for the order date. Weekends and holidays have no rate, so use the **last available rate** before that date (an as-of join).
Your ERP orders already have a `currency` column (`EUR`, from the Day 24 seed script). Treat DummyJSON prices as USD.

### 📏 Rules of the challenge
1. **The playbook is your plan.** These day cards only tell you *what* to deliver, not *how*. Don't reopen earlier weeks unless you're stuck for more than 15 minutes, and if you do, add the missing piece to the playbook.
2. **AI only for review, after you've finished the day.** Not for writing code. Use the review prompt in the [README](README.md#-using-ai-as-a-tutor-without-letting-it-learn-for-you).
3. **Timebox each day** (~60 min). Unfinished? Write down what's left and move on. Real projects have deadlines too.

| Day | Topic | Time |
|---|---|---|
| 64 | Discovery and a one-page design note | ~50 min |
| 65 | Extract, raw and validate | ~60 min |
| 66 | Transform in PySpark: rates table and as-of join | ~60 min |
| 67 | Production polish: CLI, DQ, backfill a year, Docker | ~60 min |
| 68 | 🛠 Retrospective: explain it out loud + final quiz | ~50 min |

---

<a id="day-64"></a>
## Day 64 · Discovery and a one-page design note

⏱ ~50 min · 📁 `shopflow/docs/nbp_design.md`

> 🎯 **By the end you can:** answer every discovery question for an unfamiliar API *before* writing pipeline code.
> 💼 **At work:** 30 minutes of discovery saves days of rework. Senior engineers write the design note first.

### 📖 Learn (5 min)
- Open playbook §1. That's today's agenda.
- API docs: https://api.nbp.pl/en.html. Explore in the browser or with `Invoke-RestMethod`.

### 💻 Do (40 min)
- [ ] **1.** Answer every §1 question for NBP in your own words. Probe the API to find out, don't guess:
  ```powershell
  Invoke-RestMethod "https://api.nbp.pl/api/exchangerates/tables/A/2025-12-29/2026-01-05/?format=json"
  Invoke-RestMethod "https://api.nbp.pl/api/exchangerates/tables/A/2026-01-03/?format=json"
  ```
- [ ] **2.** Find the limits yourself. What's the longest date range one request accepts for the **tables** endpoint? For the **single-currency** endpoint? What status code and message do you get when you exceed it?
- [ ] **3.** *Predict, then check:* what does the API return for a Saturday? For a range that contains only a weekend? For a currency code that doesn't exist?
- [ ] **4.** Compare a response from 2002 with one from 2026. Is the schema the same? Write down what differs.
- [ ] **5.** Write `nbp_design.md` (one page): entities and grain, endpoint you'll use and why, incremental strategy, raw layout (`raw/nbp/rates_a/load_date=.../`), contract fields and types, failure modes and how you'll handle each one, and which order date gets which rate.
- ⭐ *Stretch:* look up which rate Polish accounting uses for a transaction (same day or previous business day?) and add it as an open question for "the business".

### ✅ Check yourself (5 min)
1. What's the grain of a staging rates table?
2. A 404 from NBP can mean two different things. What are they, and how will your pipeline tell them apart?
3. NBP history doesn't change, so is incremental loading even worth it here?
4. Why store `mid` as a decimal and not a float?

<details><summary>Answers</summary>

1. One row per `(currency_code, effective_date)`, with `mid` and the table number `no`.
2. "No data for this range" (weekend, holiday) and "you asked for something wrong" (bad code or URL). Both say `NotFound`. Treat 404 as "empty" only for well-formed requests, and let a DQ check (missing business days) catch a pipeline that quietly gets nothing.
3. Yes. The full history since 2002 is ~6,000 business days. Fetching only from the last loaded date (minus a few days of lookback) is cheap and polite. Keep a `--full-refresh` for rebuilds.
4. Money. Floats can't represent `4.2274` exactly, and rounding errors add up across thousands of orders.
</details>

---

<a id="day-65"></a>
## Day 65 · Extract, raw and validate

⏱ ~60 min · 📁 `shopflow/src/shopflow/sources/nbp.py`, `shopflow/src/shopflow/validate/nbp.py`, `shopflow/tests/test_nbp.py`

> 🎯 **By the end you can:** build a connector that respects the source's limits, survives its quirks, and is tested without network calls.
> 💼 **At work:** this is the core of "integrate a new source". Everything else in the pipeline is already reusable.

### 📖 Learn (5 min)
- Use playbook §2, §3, §4 and §6. Your connector Protocol (`extract(since) -> Iterator[dict]`), `@retry` and raw writer already exist.

### 💻 Do (50 min)
- [ ] **1.** Write a pure `date_chunks(start, end, max_days) -> Iterator[tuple[date, date]]` (inclusive ranges). Test it first: `2025-01-01 → 2025-12-31` with `max_days=93` gives 4 chunks, and the last is `2025-10-07 → 2025-12-31`. Also test a 1-day range and `start > end`.
- [ ] **2.** Write `NbpConnector` that fetches each chunk, treats a 404 on a valid request as "no rows", retries timeouts, 429 and 5xx with your `@retry`, and **does not** retry 400.
- [ ] **3.** Write each chunk's response to the raw layer exactly as received, with metadata (URL, extracted_at, row count).
- [ ] **4.** Write a pydantic contract for one flattened row: `table`, `no`, `effective_date: date`, `currency_code` (3 uppercase letters), `mid: Decimal` (> 0). Bad rows go to quarantine with a reason.
- [ ] **5.** Record real responses into `tests/fixtures/nbp/` (one normal chunk, one 404, one 400). Test the connector against them with mocks: no live calls.
- [ ] **6.** Run it for last month and look at the raw files and the quarantine.
- ⭐ *Stretch:* make the schema-drift check from Week 5 flag the 2002 response shape.

<details><summary>Hints (only after you've tried)</summary>

- Chunk loop: `chunk_end = min(chunk_start + timedelta(days=max_days - 1), end)`, then `chunk_start = chunk_end + timedelta(days=1)`.
- The tables endpoint returns a **list of tables**, each with a `rates` list. Flatten with a nested loop that copies `effectiveDate` and `no` onto every rate.
</details>

### ✅ Check yourself (5 min)
1. Why does `date_chunks` deserve its own unit tests?
2. Why is retrying a 400 pointless, and a 503 sensible?
3. Your raw layer stores the nested JSON, and staging stores flat rows. Why not flatten before writing raw?
4. What would your tests miss if they only used mocks you wrote by hand?

<details><summary>Answers</summary>

1. Off-by-one errors at chunk edges silently drop or double a day. A pure function is cheap to test exhaustively.
2. A 400 means the request is wrong (like exceeding the range limit). It will fail every time. A 503 is temporary and often works on retry.
3. Raw is the "as received" record. If your flattening has a bug, you can fix it and rebuild staging from raw without calling the API again.
4. The real shape and quirks (nested lists, Polish currency names, the 404 body). Recorded responses keep tests honest.
</details>

---

<a id="day-66"></a>
## Day 66 · Transform in PySpark: rates table and as-of join

⏱ ~60 min · 📁 `shopflow/src/shopflow/spark/nbp_rates.py`, `shopflow/tests/spark/test_nbp_rates.py`

> 🎯 **By the end you can:** load a dimension incrementally with `MERGE` and join facts to it "as of" a date.
> 💼 **At work:** as-of joins (prices, FX rates, customer tiers at a point in time) are everywhere, and easy to get subtly wrong.

### 📖 Learn (5 min)
- Use playbook §5 and §6. Your Delta `MERGE` code and Spark test fixture already exist.
- As-of join, option A: build a calendar of every day, fill the gaps with `F.last("mid", ignorenulls=True)` over a window ordered by date, then do an equi-join.
- Option B: join on `rate_date <= order_date`, then keep the latest rate per order with `row_number()`. Simpler to write, but a range join can blow up.

### 💻 Do (50 min)
- [ ] **1.** `stg_nbp_rates` (Delta): read validated rows with an explicit schema, `MERGE` on `(currency_code, effective_date)`. Run it twice: same row count.
- [ ] **2.** Write `as_of_rates(rates, start, end)` (option A) that returns one row per `(currency_code, calendar_date)` with `mid` and `rate_date` (the date the rate actually came from).
- [ ] **3.** Join orders to it and compute `revenue_pln = value * mid`, rounded to 2 decimals. PLN orders get `mid = 1`. Write the result to a mart.
- [ ] **4.** Test with tiny data and `assertDataFrameEqual`. Use these rates: Fri 2025-12-19 → 3.5941, Mon 2025-12-22 → 3.5904, Tue 2025-12-23 → 3.5848, Mon 2025-12-29 → 3.5898. Orders dated Sat 12-20, Wed 12-24 and Sun 12-28 must use which rates?
- [ ] **5.** *Failure scenario:* an order is dated before your first loaded rate. What happens in your join? Make it fail loudly or flag it, never silently `null`.
- ⭐ *Stretch:* implement option B too, compare `explain()` for both, and write which you'd ship and why.

### ✅ Check yourself (5 min)
1. What do the three orders in task 4 get?
2. Why `MERGE` and not overwrite for the rates table?
3. Why keep `rate_date` in the output?
4. Option A vs option B: when does B become dangerous?

<details><summary>Answers</summary>

1. 12-20 → 3.5941 (Friday's rate). 12-24 and 12-28 → 3.5848 (Tuesday 12-23). Dec 24–26 2025 were all holidays, so there's a 6-day gap.
2. Each incremental run brings only a few new days. `MERGE` upserts them without rewriting history, and a rerun of the same days changes nothing.
3. Auditability. Finance will ask "which rate did you use for this order?", and a stale rate (a long gap) becomes visible.
4. When there are many orders and many rate dates per currency: `<=` produces every earlier rate per order before filtering, and Spark can't use a fast equi-join. Option A keeps it an equi-join on `(currency, date)`.
</details>

---

<a id="day-67"></a>
## Day 67 · Production polish: CLI, DQ, backfill a year, Docker

⏱ ~60 min · 📁 `shopflow/src/shopflow/cli.py`, `shopflow/src/shopflow/checks.py`, `shopflow/README.md`

> 🎯 **By the end you can:** run the new source like every other source, with checks that stop a bad load.
> 💼 **At work:** "done" means someone else can run it, rerun it and trust it.

### 📖 Learn (5 min)
- Use playbook §6 and §7, and your Week 11 runbook.

### 💻 Do (50 min)
- [ ] **1.** Add `nbp` to the CLI: `shopflow run --source nbp --start-date ... --end-date ...`, including `--dry-run`. The dry run should print the chunks it would request.
- [ ] **2.** DQ checks in `checks.py`: every rate `> 0`; `(currency_code, effective_date)` unique; no gap between rate dates longer than 6 calendar days (why 6? see Day 66); every order in the mart has a `revenue_pln`.
- [ ] **3.** Backfill all of 2025 with one command. How many requests did it make? Run it again and prove nothing changed.
- [ ] **4.** Break it on purpose: set the chunk size to 120 and run. Does it fail loudly with exit code `1`? Put it back.
- [ ] **5.** Run the backfill in Docker. Then add NBP to the runbook: commands, known quirks (404s, range limit) and how to rerun a failed chunk.
- [ ] **6.** Commit, push and get CI green.

### ✅ Check yourself (5 min)
1. Why is "no gap longer than 6 days" better than "a rate exists for every weekday"?
2. Your 2025 backfill with 93-day chunks made 4 requests. What would 1 request with the single-currency endpoint cost you?
3. The NBP API is down for a day. What happens to orders, and what should happen?
4. Which DQ check would catch a connector that silently treats every response as 404?

<details><summary>Answers</summary>

1. Polish holidays fall on weekdays, so "every weekday" fails on every holiday unless you maintain a holiday calendar. A max-gap rule is simple and still catches real outages.
2. The single-currency endpoint allows up to 367 days, but only for one currency, so you'd need one request per currency. The tables endpoint gets all ~30 currencies in each request.
3. The extract fails (non-zero exit), marts for that day aren't built, and the watermark doesn't move. The next run catches up. Orders shouldn't get a silently stale rate. The max-gap check would flag it.
4. The max-gap check (no rates at all for the period), plus a row-count check on the extract.
</details>

---

<a id="day-68"></a>
## Day 68 · 🛠 Retrospective: explain it out loud + final quiz

⏱ ~50 min · 📁 `plan/README.md`, `plan/new-source-playbook.md`

> 🎯 **By the end you can:** explain your whole pipeline clearly, and know exactly what to learn next.
> 💼 **At work:** being able to explain *why* you built it this way is what makes people trust your code.

### 💻 Do (40 min)
- [ ] **1.** Go through the [skills checklist](README.md#skills-checklist-your-actual-goal). Tick only what you could do **without looking anything up**.
- [ ] **2.** Fill in Week 12 in the [progress tracker](README.md#-progress-tracker). Compare your Week 1 and Week 12 confidence.
- [ ] **3.** Answer each prompt out loud in 1–2 minutes, as if to a teammate or interviewer. Record yourself on at least three:
  1. Walk me through `shopflow`, from sources to marts.
  2. How did you integrate NBP? What did you find out before writing code?
  3. How would you handle the source changing its schema?
  4. Why `MERGE` and not overwrite?
  5. What happens if the pipeline fails halfway through a backfill?
  6. How do you make sure an order gets the right exchange rate on a holiday?
  7. Your Spark job is slow. How do you find out why?
  8. How do secrets get into the container?
  9. How do you know the data is correct, not just that the job succeeded?
  10. What would you change if the data were 100 times bigger?
- [ ] **4.** Write a "Gaps" list at the bottom of your playbook: what you still had to look up this week. Each gap is your next study topic.
- [ ] **5.** Read [After Week 12](README.md#-after-week-12) and pick **one** next step for the coming month.

### ✅ Final quiz
1. What makes a load idempotent? Give two ways `shopflow` achieves it.
2. A watermark-based extract misses records that arrived late. What's the fix?
3. When do you broadcast a join in Spark, and when is it a bad idea?
4. Raw, staging, marts: one sentence each on what lives there and why you keep raw.
5. Explain out loud, as in an interview: what's an as-of join, and how did you build one?

<details><summary>Answers</summary>

1. Rerunning gives the same result. `shopflow` overwrites date partitions and uses `MERGE` on business keys, and only moves the watermark after success.
2. A lookback window: re-read the last N days and let the dedupe or `MERGE` remove the overlap.
3. When one side is small enough to copy to every executor (a dimension like rates), so the big side isn't shuffled. Bad when the "small" side is large: it can run the driver or executors out of memory.
4. Raw: data exactly as received, so you can rebuild without calling the source again. Staging: typed, validated, deduped. Marts: business-ready tables for reports.
5. Joining each fact to the latest dimension row at or before its date. I built a daily calendar per currency, filled weekends and holidays with the last known rate using a window, then did a normal equi-join. I kept `rate_date` for auditing.
</details>

---

## 🏁 End of week 12: I can…
- [ ] Discover an unfamiliar source and write a design note before coding
- [ ] Build a tested connector that respects limits and survives quirks
- [ ] Load it incrementally into Delta and join facts to it "as of" a date
- [ ] Run it from the CLI and in Docker, with DQ checks and a runbook
- [ ] Explain every design choice out loud

📈 Rate your confidence for Week 12 in the [progress tracker](README.md#-progress-tracker).

---

**You did it.** Twelve weeks ago, a new data source was a scary unknown. This week you took one from "what is this?" to a tested, containerised pipeline, on your own. That's the job. Keep the playbook, keep filling in the gaps list, and the next new source will be easier still. 🎉

# Week 12 — Senior polish and interview readiness

You've built the skills. This week is about **showing** them: clean code, a portfolio-quality README, system design thinking, and timed problem-solving.

---

## Day 64 — Review your own project like a senior 🔁

**Do (45 min)**
1. Read through all of `shopflow/src` as if it were a teammate's PR. Write `REVIEW.md` with at least 8 findings, sorted by severity. Check for:
   - unclear names, functions over ~40 lines, duplicated logic
   - missing tests for failure paths
   - hard-coded values, bare `except`, `print` instead of logging
   - anything that isn't idempotent
2. Fix the top 3. Commit each fix separately with a clear message.
3. Ask Claude for its own review. Compare it with yours: what did it find that you missed, and what did you find that it missed?

**Check yourself**
1. What's the difference between a junior and a senior code review comment?
2. Why make small, separate commits?

<details><summary>Answers</summary>

1. A junior comment says *what* ("rename this"). A senior comment explains *why* and the impact ("this isn't idempotent: a retry will duplicate rows in X"), and prioritises: correctness > reliability > maintainability > style.
2. They're easier to review, easier to revert, and the history explains itself.
</details>

---

## Day 65 — Portfolio README 🛠

**Do (45 min)** Rewrite the `shopflow` README for a hiring manager who spends 2 minutes on it:
1. **One-paragraph pitch** at the top: what it does and what it demonstrates.
2. **Architecture diagram** in Mermaid (GitHub renders it):
   ````markdown
   ```mermaid
   flowchart LR
     API[DummyJSON API] --> RAW[raw JSON]
     RAW --> VAL{pydantic validation}
     VAL -->|valid| STG[(DuckDB staging)]
     VAL -->|invalid| Q[quarantine]
     STG --> DQ[data quality checks] --> MARTS[(marts)]
     STG --> LLM[LLM enrichment + cache] --> MARTS
     MARTS --> ASK[text-to-SQL / MCP]
   ```
   ````
3. **Key engineering decisions & trade-offs:** idempotency strategy, why DuckDB, threads vs async, LLM caching and evals.
4. **How to run** (3 commands) + CI badge.
5. **What I'd do at 100x scale:** object storage (S3/GCS) + Parquet/Iceberg, Spark or a cloud warehouse, Airflow/Dagster on a schedule, monitoring and alerting, dbt for marts, a secrets manager.
6. Pin the repo on your GitHub profile and add it to your CV.

**Check yourself:** can you explain each "decision & trade-off" bullet out loud for 1 minute without notes?

---

## Day 66 — Data engineering system design 🧠

**Learn (15 min)** A framework for any design question:
1. **Clarify requirements:** data volume, freshness (batch or real time?), consumers, SLAs, budget
2. **Sources & ingestion:** APIs, databases (CDC), events (Kafka); push vs pull
3. **Storage:** lake (object storage + Parquet/Iceberg) vs warehouse; partitioning
4. **Processing:** batch (Spark/SQL/dbt) vs streaming (Kafka + Flink/Spark Streaming)
5. **Serving:** marts, BI, APIs, reverse ETL, ML features
6. **Orchestration, data quality, monitoring, lineage**
7. **Failure modes:** late data, duplicates, backfills, schema changes, reprocessing
8. **Cost & security:** PII, access control, retention

**Do (30 min, out loud or written)**
> *"expondo-like marketplace: design a pipeline that ingests ~50M orders/day from 3 marketplace APIs and a website clickstream. Finance needs daily reports by 7:00. Ops needs stock alerts within 5 minutes. Product wants AI-generated product attributes."*

Use the framework. Set a 25-minute timer. Then ask Claude to play a skeptical interviewer and challenge your design:
> "You're a senior data engineering interviewer. Here's my design: [paste]. Ask me 5 hard follow-up questions, one at a time."

**Check yourself**
1. Why does this case need *both* batch and streaming?
2. Where would you put the LLM attribute enrichment, and how would you keep its cost bounded?
3. How do you guarantee no duplicate orders in the finance report?

<details><summary>Answers</summary>

1. Finance needs complete, reconciled daily data (batch is cheaper and simpler). Stock alerts need low latency (streaming). Choose per requirement, not per hype.
2. As an asynchronous batch step on **new or changed products only** (incremental), with content-hash caching, a small model, a batch API, evals and a budget guard. Never in the latency-critical path.
3. Idempotent loads keyed on `order_id` (MERGE/upsert or dedupe with `ROW_NUMBER`), plus uniqueness data-quality checks before publishing, and reconciliation of counts against the source.
</details>

---

## Day 67 — Timed coding mock 🧠

**Do (45 min, timer, no AI)** in `src/day67/mock.py`. Write tests for each problem.

**Problem 1: Sessionize (15 min).** Events are sorted by user, then timestamp. A new session starts when the gap is more than 30 minutes. Return `{user_id: number_of_sessions}`.
```python
events = [("u1", "2026-10-21 10:00"), ("u1", "2026-10-21 10:20"), ("u1", "2026-10-21 11:15"),
          ("u2", "2026-10-21 09:00"), ("u2", "2026-10-21 09:10")]
# → {"u1": 2, "u2": 1}
```

**Problem 2: Merge overlapping promotions (15 min).** Given `[(start_day, end_day), ...]`, merge overlapping or touching ranges.
```python
[(1, 3), (2, 5), (8, 10), (10, 12), (15, 15)]  # → [(1, 5), (8, 12), (15, 15)]
```

**Problem 3: Flatten nested JSON (15 min).**
```python
{"id": 1, "user": {"name": "Anna", "address": {"city": "Berlin"}}, "tags": ["a", "b"]}
# → {"id": 1, "user.name": "Anna", "user.address.city": "Berlin", "tags": ["a", "b"]}
```

**Afterwards:** explain the time complexity of each solution, then get it reviewed by Claude.

<details><summary>Solution hints (only after the timer!)</summary>

1. Loop with `prev_user`/`prev_time`. Increment when the user changes or `curr - prev > timedelta(minutes=30)`. Parse dates with `datetime.strptime`. O(n).
2. Sort by start. If `start <= last_end + 1`, extend `last_end = max(last_end, end)`, otherwise start a new range. O(n log n).
3. A recursive function `flatten(d, prefix="")`: if a value is a dict, recurse with `f"{prefix}{key}."`, otherwise assign it. O(total keys).
</details>

---

## Day 68 — Final review and your story 🔁

**Do (45 min)**
1. **Re-take a quiz from each week** (pick any 2 questions per week, 24 in total). Mark the ones you'd still hesitate on, and re-read those days.
2. **Compare:** open `src/day1/exercises.py` and your `shopflow` code side by side. Write 5 sentences about what changed.
3. **Your project pitch (STAR, 2 minutes):** *Situation* (wanted hands-on senior-level skills) → *Task* (build a production-style pipeline) → *Action* (idempotent ELT, validation and quarantine, DQ, concurrency, LLM enrichment with evals, CI/Docker) → *Result* (what it does, what you learned, what you'd do at scale). Record yourself once.
4. Prepare answers to:
   - "Tell me about a hard bug you fixed." (Use one from this plan!)
   - "How do you ensure data quality?"
   - "How have you used AI in data engineering?"
   - "What would you improve in your project?"
5. Update your CV skills section with what you can now **defend in an interview**.

**Final self-check:** can you explain each of these in 1 minute?
idempotency · incremental loads & watermarks · generators · decorators · context managers · GIL & concurrency · pydantic validation · window functions · Parquet/partitioning · data-quality checks · orchestration/DAGs · LLM structured outputs, caching & evals · RAG · prompt-injection guardrails · Docker & CI

If yes, you're ready to apply. 🎉

📝 Final confidence log entry. Compare it with Week 1.

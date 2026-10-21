# Week 8 — Production-grade pipeline

This week turns a script into something you could run in production: configurable, runnable from the command line, incremental and orchestrated. These are the topics senior interviews dig into.

---

## Day 44 — Configuration and secrets 🛠

**Learn (10 min)**
- **12-factor config:** settings come from environment variables, not from the code.
- `.env` file for local development (gitignored) + a committed `.env.example` that shows the names but no values.
- `pydantic-settings` reads env vars into a typed `Settings` class. `SecretStr` hides values in logs and reprs.

**Do (30 min)**
1. `uv add pydantic-settings`
2. `config.py`:
   ```python
   class Settings(BaseSettings):
       model_config = SettingsConfigDict(env_file=".env", env_prefix="SHOPFLOW_")
       base_url: str = "https://dummyjson.com"
       data_dir: Path = Path("data")
       db_path: Path = Path("data/warehouse.duckdb")
       page_size: int = 50
       log_level: str = "INFO"
       anthropic_api_key: SecretStr | None = None
   ```
3. Replace every hard-coded value in the pipeline with `settings.x`.
4. Create `.env.example`, and make sure `.env` is in `.gitignore`. Change `SHOPFLOW_PAGE_SIZE=20` in `.env` and confirm the behaviour changes.

**Check yourself**
1. Why put config in env vars instead of code?
2. You accidentally pushed an API key to GitHub. What do you do?
3. What does `SecretStr` protect against?
4. Why commit `.env.example`?

<details><summary>Answers</summary>

1. The same code runs in dev, test and prod with different settings. Secrets stay out of git. Changing a setting doesn't need a code change.
2. **Rotate (revoke) the key immediately.** Deleting the commit isn't enough, because it's already been scraped or cached. Then remove it from the history and add secret scanning.
3. Accidentally printing or logging the secret (`print(settings)` shows `**********`).
4. Documentation: new developers can see which variables exist and need setting.
</details>

---

## Day 45 — Command-line interface and backfills 🛠

**Learn (10 min)**
- A CLI makes the pipeline runnable by people, schedulers and containers.
- `typer` (built on type hints) or the standard library's `argparse`.
- **Exit codes:** `0` = success, non-zero = failure. Schedulers rely on them.
- **Backfill:** re-running the pipeline for past dates.

**Do (35 min)**
1. `uv add typer`
2. `cli.py`:
   - `shopflow run --date 2026-10-21 --steps extract,validate,load,check,transform`
   - `shopflow backfill --start 2026-10-01 --end 2026-10-07` (loops over the dates and calls run)
3. Add `[project.scripts] shopflow = "shopflow.cli:app"` to `pyproject.toml`, then `uv run shopflow --help`.
4. Make sure a failure exits with code 1. Check with `echo $LASTEXITCODE` (PowerShell) after a forced error.

**Check yourself**
1. Why do exit codes matter?
2. What makes a pipeline safe to backfill?
3. Why pass `--date` explicitly instead of always using "today"?
4. argparse vs typer?

<details><summary>Answers</summary>

1. Schedulers, CI and shell scripts decide whether something succeeded, retried or alerted based on the exit code. A crash that exits 0 looks like success.
2. Idempotent, date-partitioned steps that depend only on the date given, not on "now."
3. Reproducibility and backfills. A run for 2026-10-01 should produce the same result whenever it's executed.
4. argparse is in the standard library and more verbose. typer gives a cleaner API from type hints, with nicer help output.
</details>

---

## Day 46 — Incremental loads and state 🧠🛠

**Learn (15 min)**
- **Full load:** reload everything every time. Simple, but expensive at scale.
- **Incremental:** only fetch new or changed records since the last **watermark** (e.g. `max(updated_at)`).
- **Late-arriving data:** records with old timestamps that show up later → use a **lookback window** (re-read the last N hours or days) + **upsert** to dedupe.
- **CDC (change data capture):** reading changes from the database log.

DummyJSON is static, so you'll simulate a source with changing data.

**Do (40 min)** in `src/shopflow/incremental.py`
1. Fake source: `FakeOrderSource` (your Week 5 Protocol!) that yields orders with `order_id`, `value` and `updated_at`. Some orders get **updated** on later days.
2. `_pipeline_state(source TEXT PRIMARY KEY, watermark TIMESTAMP)` table.
3. `run_incremental(con, source, lookback=timedelta(days=1))`:
   - read the watermark → fetch records with `updated_at > watermark - lookback`
   - **upsert** into `orders` (`ON CONFLICT (order_id) DO UPDATE`)
   - update the watermark to the max `updated_at` seen, **only after the load commits**
4. Tests: run day 1 → day 2 → re-run day 2 → assert there are no duplicates and the updated values win.

**Check yourself**
1. What is a watermark?
2. Why use a lookback window?
3. Why update the watermark only after a successful load?
4. Full vs incremental: what's the trade-off?

<details><summary>Answers</summary>

1. The stored position up to which data has already been processed (e.g. the latest `updated_at`).
2. To catch late-arriving or slightly out-of-order records. The upsert dedupes the overlap.
3. If you update it first and the load fails, the next run skips that data forever: **silent data loss**.
4. Full is simple and self-healing, but slow and expensive. Incremental is efficient, but more complex (state, late data, deletes are hard to detect).
</details>

---

## Day 47 — Orchestration 🧠🛠

**Learn (15 min)**
- **DAG:** tasks with dependencies, without cycles.
- An orchestrator handles: schedules, retries, dependencies, backfills, logs, alerting, a UI.
- **Airflow** (most common in job ads), **Dagster** (asset-based, modern), **Prefect** (Pythonic, lightweight).
- Airflow concepts: `DAG`, operators/`@task`, `schedule`, `logical_date` (the data interval the run is *for*), `catchup`.

**Do (35 min)**
1. `uv add prefect`. Wrap the steps as `@task`s (with `retries=2`) inside a `@flow` that takes `run_date`. Run it locally. Optionally, `prefect server start` to view the UI.
2. **Read and translate:** here's an Airflow DAG. Write a comment above each line explaining it, and map it to your Prefect flow.
   ```python
   from airflow.decorators import dag, task
   import pendulum

   @dag(schedule="0 6 * * *", start_date=pendulum.datetime(2026, 10, 1), catchup=True)
   def shopflow_daily():
       @task(retries=2)
       def extract(ds=None): ...
       @task
       def load(ds=None): ...
       @task
       def transform(ds=None): ...
       extract() >> load() >> transform()

   shopflow_daily()
   ```

**Check yourself**
1. What is a DAG?
2. Why keep tasks small and idempotent?
3. In Airflow, a run scheduled for 06:00 on Oct 22 with a daily schedule processes which day's data?
4. What does `catchup=True` do?

<details><summary>Answers</summary>

1. A directed acyclic graph: tasks plus dependency arrows, with no loops.
2. Retries and backfills re-run single tasks safely, and failures are easier to pinpoint.
3. Usually Oct 21. The `logical_date` marks the **start of the data interval**, and the run happens when that interval ends. This trips many people up.
4. It creates runs for every missed interval between `start_date` and now (an automatic backfill).
</details>

---

## Day 48 — Week 8 review 🔁

**Do (30 min):** update the README with **How to run** (CLI examples), **Configuration** and **Orchestration**. Tag a release: `git tag v0.1.0`.

**Weekly quiz**
1. Walk through what happens, step by step, when you run `shopflow backfill` for 7 days.
2. Where does `shopflow` store state, and what happens if that state is lost?
3. Explain idempotency in 3 different steps of your pipeline.
4. A task fails halfway through. What does the orchestrator do, and why is that safe in your design?
5. List 3 things in your pipeline that are configurable without code changes.

<details><summary>Answers</summary>

1. (Yours.) The CLI parses the dates → loops → each day: extract to the raw partition, validate, delete-insert load, checks, rebuild marts → exit code.
2. The `_pipeline_state` watermark (incremental) and the raw files. If the watermark is lost, you can rebuild it from `max(updated_at)` in the target, or do a full reload.
3. Extract overwrites the date partition. Load deletes and inserts by `_run_date` in a transaction. Incremental upserts by key and moves the watermark only after commit.
4. It retries the task. That's safe because each task overwrites its own outputs and doesn't append.
5. Base URL, page size, data dir, DB path, log level, API key.
</details>

📝 Confidence log. You've built a real pipeline: extract → validate → load → DQ → transform, idempotent and configurable.

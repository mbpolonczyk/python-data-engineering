# Week 11 · Production-ready ETL

**Phase 5 — Production & proof** · Days 59–63
[← Week 10](week-10-pyspark-performance-delta.md) · [Plan overview](README.md) · [Week 12 →](week-12-final-challenge.md)

> **This week's outcome:** `shopflow` stops being "code that works on my laptop". It reads config from the environment, runs from a CLI, recovers from a failed day, and runs the same way in Docker and in CI.
>
> **Project milestone:** `shopflow run --source dummyjson --start-date 2026-10-01 --end-date 2026-10-07` works in Docker, and your README has a runbook. Playbook §7 is filled in.

| Day | Topic | Time |
|---|---|---|
| 59 | Config and secrets with pydantic-settings | ~45 min |
| 60 | A CLI with typer: runs, backfills, dry-run, exit codes | ~50 min |
| 61 | Orchestration, state and logging | ~50 min |
| 62 | Docker and GitHub Actions CI | ~55 min |
| 63 | 🛠 Build day: end to end in Docker + runbook + quiz | ~60 min |

---

<a id="day-59"></a>
## Day 59 · Config and secrets with pydantic-settings

⏱ ~45 min · 📁 `shopflow/src/shopflow/config.py`, `shopflow/.env.example`

> 🎯 **By the end you can:** run the same code in dev and prod just by changing environment variables, with no tokens in git.
> 💼 **At work:** a leaked token in a repo is a security incident. Hardcoded paths are why "it works on my machine".

### 📖 Learn (10 min)
- **Config comes from the environment, not the code.** Code is the same everywhere. Only the settings change.
- `.env` holds your local values and is **gitignored**. `.env.example` holds the names with fake values and **is committed**.
- `pydantic-settings` reads env vars into a typed class. A wrong type fails at startup, not halfway through a run.
- `SecretStr` prints as `**********`. Call `.get_secret_value()` only where you actually send the token.
- Docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

### 💻 Do (30 min)
- [ ] **1.** `uv add pydantic-settings`, then create `config.py`:
  ```python
  from pathlib import Path
  from pydantic import SecretStr
  from pydantic_settings import BaseSettings, SettingsConfigDict

  class Settings(BaseSettings):
      model_config = SettingsConfigDict(env_prefix="SHOPFLOW_", env_file=".env")
      env: str = "dev"
      data_dir: Path = Path("data")
      dummyjson_url: str = "https://dummyjson.com"
      dummyjson_token: SecretStr | None = None
      page_size: int = 50
      log_level: str = "INFO"
  ```
- [ ] **2.** Replace every hardcoded value in your connectors and raw writer (base URLs, `data/` paths, page sizes) with `settings.x`. Search for leftovers: `Get-ChildItem src -Recurse -Filter *.py | Select-String "data/|https://"`.
- [ ] **3.** Per-environment config: create `.env.prod` with `SHOPFLOW_ENV=prod` and `SHOPFLOW_DATA_DIR=data_prod`. Load it with `Settings(_env_file=".env.prod")`. Confirm that the raw files land in `data_prod/`.
- [ ] **4.** Precedence test. In PowerShell: `$env:SHOPFLOW_PAGE_SIZE = "20"`, then print `Settings().page_size`. Which wins, the env var or `.env`? Clean up with `Remove-Item Env:SHOPFLOW_PAGE_SIZE`.
- [ ] **5.** Commit `.env.example`, check `.env*` (except the example) is in `.gitignore`, and prove it with `git status`. Then, in playbook §7, note where secrets live and how a teammate finds the variable names.
- ⭐ *Stretch:* add a `@field_validator` that fails if `env == "prod"` and `data_dir` is still the default `data`.

### ✅ Check yourself (5 min)
1. What does `print(Settings())` show for `dummyjson_token`?
2. Which wins: a real environment variable or the same name in `.env`?
3. Why fail at startup on a bad setting instead of when it's first used?
4. You pushed a token to GitHub an hour ago. What do you do, in order?

<details><summary>Answers</summary>

1. `SecretStr('**********')`. The value is hidden in prints, reprs and logs.
2. The real environment variable. `.env` is only a fallback, which is what lets Docker or CI override local values.
3. A typo in prod should stop the run in the first second, not after an hour of extracting, and not with half-written output.
4. **Revoke or rotate the token first.** It's already been scraped. Then remove it from the code and history, add it to `.env`, and turn on secret scanning.
</details>

---

<a id="day-60"></a>
## Day 60 · A CLI with typer: runs, backfills, dry-run, exit codes

⏱ ~50 min · 📁 `shopflow/src/shopflow/cli.py`

> 🎯 **By the end you can:** run one day or a range of days from the command line, preview it with `--dry-run`, and signal failure with an exit code.
> 💼 **At work:** schedulers, containers and on-call engineers all run your pipeline through its CLI. A crash that exits with `0` looks like success.

### 📖 Learn (10 min)
- `typer` builds a CLI from type hints. Parameter `start_date` becomes the option `--start-date`.
- **Backfill** = rerunning past dates. It's only safe if each day is idempotent (Week 6, Week 10 `MERGE`).
- **Exit codes:** `0` success, `1` failure. Typer uses `2` for bad usage. Pick one extra code for "data-quality failed" if you like.
- In PowerShell, check the last exit code with `$LASTEXITCODE`.
- Docs: https://typer.tiangolo.com/tutorial/

### 💻 Do (35 min)
- [ ] **1.** `uv add typer`. Start `cli.py`:
  ```python
  from datetime import datetime, timedelta
  import typer

  app = typer.Typer()

  @app.callback()
  def main() -> None:
      """shopflow pipeline."""   # keeps `run` as a subcommand

  @app.command()
  def run(
      source: str = typer.Option(..., help="dummyjson, erp, supplier, clickstream"),
      start_date: datetime = typer.Option(..., formats=["%Y-%m-%d"]),
      end_date: datetime | None = typer.Option(None, formats=["%Y-%m-%d"]),
      dry_run: bool = False,
  ) -> None:
      ...
  ```
- [ ] **2.** Write a pure helper `days_between(start, end) -> list[date]` (inclusive). Test it: `2026-10-30 → 2026-11-02` gives 4 days. `end < start` raises `typer.BadParameter`.
- [ ] **3.** Loop over the days and call your existing pipeline function for each one. With `--dry-run`, only log what *would* run (source, day, output path) and touch nothing.
- [ ] **4.** On any failure, log it and `raise typer.Exit(code=1)`. Decide: does a backfill stop at the first failed day, or continue and report all failures at the end? Write your choice in a docstring.
- [ ] **5.** Register the script in `pyproject.toml` (`[project.scripts]` → `shopflow = "shopflow.cli:app"`), then try it:
  ```powershell
  uv run shopflow run --help
  uv run shopflow run --source dummyjson --start-date 2026-10-01 --end-date 2026-10-03 --dry-run
  uv run shopflow run --source nope --start-date 2026-10-01; $LASTEXITCODE
  ```
- [ ] **6.** Test the CLI with `typer.testing.CliRunner`: assert `result.exit_code == 0` for a dry run and `!= 0` for an unknown source.
- ⭐ *Stretch:* add `--full-refresh`, which ignores the saved watermark for that run only.

### ✅ Check yourself (5 min)
1. What does `$LASTEXITCODE` show after `raise typer.Exit(code=1)`?
2. Why take `--start-date` explicitly instead of always using "today"?
3. A 30-day backfill fails on day 12. With your design, what state are days 1–11 in? Can you safely rerun all 30?
4. Fail fast or continue on error in a backfill: what's the trade-off?

<details><summary>Answers</summary>

1. `1`. Schedulers and CI read exactly this to decide "failed".
2. Reproducibility. A run for 2026-10-01 must give the same result whenever it runs, and backfills need any date.
3. Days 1–11 are complete. Because each day overwrites its own partition or uses `MERGE`, rerunning all 30 gives the same result as running only 12–30.
4. Fail fast stops a systemic problem (bad token) from failing 30 times. Continue-on-error finishes the healthy days and gives a full failure list. Either way, exit non-zero if any day failed.
</details>

---

<a id="day-61"></a>
## Day 61 · Orchestration, state and logging

⏱ ~50 min · 📁 `shopflow/src/shopflow/pipeline.py`, `shopflow/src/shopflow/logging_setup.py`

> 🎯 **By the end you can:** describe your pipeline as a DAG, explain what happens when it dies halfway, and talk about Airflow and Dagster at work.
> 💼 **At work:** "What happens if it fails in the middle?" is the most common design-review and interview question for pipelines.

### 📖 Learn (15 min)
- A **DAG** is tasks plus dependencies, with no cycles: `extract → validate → stage → marts → dq`.
- An **orchestrator** (Airflow, Dagster, Prefect) adds schedules, retries, backfills, a UI and alerts. It does **not** make your tasks idempotent. That's your job.
- **The state rule:** move the watermark (Week 4) **only after** the whole run succeeds. Move it first, and a failure means silent data loss.
- **Structured logs:** one JSON object per line with `run_id`, `source`, `day`, `step`, `rows`, `duration_s`. Easy to search at 3 a.m.
- **Alert on symptoms, not only crashes:** a run that "succeeds" with 0 rows, or data that is 2 days stale, also needs an alert.

### 💻 Do (30 min)
- [ ] **1.** In `pipeline.py`, write `run_day(source, day, settings)` that calls the steps in order. Each step is its own function and logs `step`, `rows` and `duration_s`.
- [ ] **2.** Write a JSON formatter in `logging_setup.py` (subclass `logging.Formatter`, `json.dumps` a dict with `ts`, `level`, `msg` and any `extra` fields). Generate a `run_id` with `uuid.uuid4().hex[:8]` once per CLI call.
- [ ] **3.** *Failure drill:* make `stage` raise on purpose. Then answer in a comment: which files exist now? Did the watermark move? Remove the error and rerun. Is the result identical to a clean run? Prove it with a row count and a dupe check.
- [ ] **4.** *Read only, no install:* annotate each line of this Airflow 3 DAG with a comment, and map each task to your `pipeline.py` function.
  ```python
  from airflow.sdk import dag, task
  import pendulum

  @dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=True)
  def shopflow_daily():
      @task(retries=2)
      def extract(ds=None): ...          # ds = the logical date as "YYYY-MM-DD"
      @task
      def transform(ds=None): ...        # validate + stage + marts
      @task
      def dq(ds=None): ...
      extract() >> transform() >> dq()

  shopflow_daily()
  ```
- [ ] **5.** *Read only:* the same idea in Dagster thinks in **assets** (tables), not tasks. Write 3 sentences: how is `@dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2026-10-01"))` on `stg_erp__orders` different from an Airflow task? (Docs: https://docs.dagster.io/guides/build/assets)
- [ ] **6.** Playbook §7: write your "logs useful at 3 a.m." checklist.
- ⭐ *Stretch:* write a `check_freshness(max_age_days=1)` that exits non-zero if the newest mart day is too old.

### ✅ Check yourself (5 min)
1. Your run crashed after `stage` but before `marts`. What must be true for a plain rerun to fix it?
2. Why must the watermark move last?
3. Airflow, daily schedule: the run for logical date Oct 21 processes which data, and roughly when does it run?
4. Name one failure that exits `0` and how you'd catch it.

<details><summary>Answers</summary>

1. Every step is idempotent (overwrite the partition or `MERGE`) and the watermark didn't move. Then the rerun redoes the same work and ends in the same state.
2. If it moves first and a later step fails, the next run starts after data that never landed. That's silent data loss.
3. The data interval Oct 21 00:00 – Oct 22 00:00. It runs after that interval ends, around Oct 22 00:00. The logical date is the *start* of the interval.
4. The API returns an empty list, so 0 rows load "successfully". Catch it with a row-count DQ check or a freshness alert.
</details>

---

<a id="day-62"></a>
## Day 62 · Docker and GitHub Actions CI

⏱ ~55 min · 📁 `shopflow/Dockerfile`, `shopflow/.dockerignore`, `.github/workflows/ci.yml`

> 🎯 **By the end you can:** build an image that runs `shopflow` including Spark, and have every push run lint, types and tests.
> 💼 **At work:** "it runs in the container and CI is green" is the bar for merging pipeline code.

### 📖 Learn (10 min)
- **Image** = a recipe (filesystem + command). **Container** = a running instance.
- Copy `pyproject.toml` and `uv.lock` first and install, *then* copy the code. Code changes then reuse the cached dependency layer.
- PySpark needs **Java** in the image. Python's slim image doesn't have it, so install a headless JRE.
- Secrets go in at **runtime** (`--env-file`), never via `COPY .env` or `ENV TOKEN=...`.
- CI must not call real APIs. Use your recorded responses and mocks (Weeks 3–4).
- Docs: https://docs.astral.sh/uv/guides/integration/docker/ · https://docs.github.com/actions

### 💻 Do (40 min) *(needs Docker Desktop and a GitHub repo)*
- [ ] **1.** `shopflow/Dockerfile`:
  ```dockerfile
  FROM python:3.12-slim
  RUN apt-get update \
   && apt-get install -y --no-install-recommends default-jre-headless procps \
   && rm -rf /var/lib/apt/lists/*
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
  WORKDIR /app
  COPY pyproject.toml uv.lock ./
  RUN uv sync --locked --no-dev --no-install-project
  COPY src ./src
  RUN uv sync --locked --no-dev
  ENTRYPOINT ["uv", "run", "--no-sync", "shopflow"]
  ```
  Then `.dockerignore`: `data*/`, `.env*`, `!.env.example`, `.venv/`, `.git/`, `__pycache__/`.
- [ ] **2.** Build and run (PowerShell, from `shopflow/`):
  ```powershell
  docker build -t shopflow .
  docker run --rm --env-file .env -v "${PWD}/data:/app/data" shopflow run --source dummyjson --start-date 2026-10-01 --dry-run
  docker run --rm --entrypoint java shopflow -version
  ```
- [ ] **3.** Change one line of code and rebuild. Which layers say `CACHED`?
- [ ] **4.** `.github/workflows/ci.yml` (versions checked Nov 2026; bump if newer):
  ```yaml
  name: CI
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      defaults: { run: { working-directory: shopflow } }
      steps:
        - uses: actions/checkout@v7
        - uses: actions/setup-java@v6
          with: { distribution: temurin, java-version: "17" }
        - uses: astral-sh/setup-uv@v10
        - run: uv sync --locked
        - run: uv run ruff check .
        - run: uv run ruff format --check .
        - run: uv run mypy src
        - run: uv run pytest -q
  ```
- [ ] **5.** Make sure your Spark `conftest.py` fixture uses `master("local[1]")`, `spark.sql.shuffle.partitions=1` and `spark.ui.enabled=false`, so CI is fast. Push, and fix whatever fails (the first run usually fails: that's normal). Note the Java gotcha in playbook §7.
- ⭐ *Stretch:* Delta's jars download from Maven on the first Spark start. Bake them into the image by running a tiny "start Spark with Delta and stop" script during the build, then run the container with `--network none` to prove it.

### ✅ Check yourself (5 min)
1. Why install dependencies before copying `src/`?
2. The container runs, but the files it wrote are gone afterwards. Why, and what's the fix?
3. Why `ruff format --check` in CI and not `ruff format`?
4. Your Spark tests pass locally but CI hangs for 6 minutes. What two things do you check first?

<details><summary>Answers</summary>

1. Docker caches layers. Dependencies rarely change, so the slow install is reused when only your code changes.
2. A container's filesystem is temporary. Mount a volume (`-v host:container`) for `data/`, or write to object storage.
3. CI should *check* and fail, not quietly rewrite code that nobody reviews.
4. That Java is installed (`setup-java`) and that the session is small (`local[1]`, few shuffle partitions, one session per test run via a `session`-scoped fixture). Also check that no test calls a real API.
</details>

---

<a id="day-63"></a>
## Day 63 · 🛠 Build day: end to end in Docker + runbook + quiz

⏱ ~60 min · 📁 `shopflow/README.md`, `shopflow/` (whole project)

> 🎯 **By the end you can:** run the full pipeline in a container for one day and for a backfill, and tell someone else how to recover a failed day.
> 💼 **At work:** a runbook is what lets a teammate fix your pipeline while you're on holiday.

### 💻 Do (45 min)
- [ ] **1.** In Docker, run one day for every source you have, then check the marts with a quick DuckDB or Spark query.
- [ ] **2.** In Docker, run a 7-day backfill. Run it **again**. Row counts and a duplicate check must be identical.
- [ ] **3.** Add a `## Runbook` section to `shopflow/README.md`:
  - how to run one day, a backfill and a dry run (exact commands)
  - **how to rerun a failed day**: find it in the logs (`run_id`, `day`, `step`), fix, rerun the same command, verify with counts
  - where state lives, and how to reset a watermark safely
  - exit codes and what each one means
- [ ] **4.** Ask a friend, or AI, to follow the runbook literally, without your help. Fix every step where they get stuck.
- [ ] **5.** Finish playbook §7, and make sure every box in §1–§7 has a note. Week 12 relies on it.
- [ ] **6.** Afterwards, ask Claude for a review with the README review prompt. Fix the top issue.

### ✅ Weekly quiz
1. Explain out loud, as in an interview: how do config and secrets get from your laptop to the Docker container and to CI, without ever being in git?
2. Why is a backfill safe in your pipeline? Name the two properties that make it safe.
3. A run writes raw files, then fails in `marts`. Walk through what the logs show, the state of each layer, and the recovery steps.
4. Airflow and Dagster: what does each one add, and what does neither do for you?
5. Why does the Docker image need Java, and why does CI need `setup-java`?

<details><summary>Answers</summary>

1. Settings are a typed `Settings` class. Locally, values come from a gitignored `.env`. Docker gets them at runtime via `--env-file` or `-e`. CI uses GitHub Secrets as env vars, and ideally needs none because tests use recorded responses. `.env.example` documents the names.
2. Each day is **idempotent** (overwrite the partition or `MERGE` on a key) and **depends only on the date given**, not on "now". The watermark only moves after success.
3. The logs show `run_id`, `day`, `step=marts` and the error. Raw and staging for that day exist and are correct. Marts are stale for that day. The watermark didn't move. Fix the cause, rerun the same command, then verify counts and DQ.
4. They add scheduling, retries, dependencies, backfill UIs, logs and alerting. Airflow thinks in tasks, Dagster in assets (tables). Neither makes your steps idempotent or your data correct. That's your code and your DQ checks.
5. PySpark is a Python wrapper around Spark, which runs on the JVM. Without Java, `SparkSession` can't start.
</details>

---

## 🏁 End of week 11: I can…
- [ ] Load typed config from env vars and `.env`, with secrets hidden and out of git
- [ ] Run one day, a backfill or a dry run from the CLI, with correct exit codes
- [ ] Explain what happens on a mid-run failure, and why reruns are safe
- [ ] Build and run `shopflow` in Docker, and have CI check every push
- [ ] Hand someone a runbook they can follow without me

📈 Rate your confidence for Week 11 in the [progress tracker](README.md#-progress-tracker).

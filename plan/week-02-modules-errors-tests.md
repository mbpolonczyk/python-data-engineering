# Week 2 — Code that lasts: files, modules, errors, tests

So far, everything has lived in single scripts. Production code is split into modules, logs instead of printing, fails clearly, and has tests. This is the biggest gap between "can code" and "senior."

---

## Day 14 — `pathlib` and CSV 🧠

**Learn (10 min)**
- `from pathlib import Path`. Build paths with the `/` operator: `Path("data") / "raw" / "orders.csv"`
- `.exists()`, `.mkdir(parents=True, exist_ok=True)`, `.glob("*.csv")`, `.read_text()`, `.stem`, `.name`
- `Path(__file__).parent` is the folder **this script** lives in, no matter where you run it from.
- `csv.DictReader` / `csv.DictWriter`. Always use `open(path, newline="", encoding="utf-8")`.

**Do (30 min)** in `src/day14/exercises14.py`
1. Define `DATA_DIR = Path(__file__).parent / "data"` and create the folder.
2. Write the Day 7 `orders` to `orders.csv` with `DictWriter`.
3. Read it back with `DictReader`. Print `type(row["value"])`. Convert the values properly.
4. Write 3 files (`orders_2026-10-01.csv`, `…02`, `…03`) with different rows. Then read **all** of them with `glob`, adding a `source_file` field to each row. Sort the file list so the order is deterministic.

**Stretch:** your Day 3 code uses `"src/day3/orders.json"`. Run it from inside `src/day3/` and watch it fail. Fix it with `Path(__file__)`.

**Check yourself**
1. Why does the `csv` module need `newline=""`?
2. What type are the values that `DictReader` gives you?
3. Why is `Path(__file__).parent / "x.json"` more robust than `"src/day3/x.json"`?
4. What does `mkdir(parents=True, exist_ok=True)` do?

<details><summary>Answers</summary>

1. The csv module handles line endings itself. Without `newline=""`, Windows writes extra blank rows (`\r\r\n`).
2. Always `str` (or `None`/the `restval` default for missing fields). CSV has no types, so converting them is your job.
3. A plain relative path depends on the *current working directory*, which changes depending on where you run the script. `__file__` is fixed.
4. It creates any missing parent folders, and doesn't fail if the folder already exists. That makes it safe to rerun, which is a tiny example of idempotency.
</details>

---

## Day 15 — Modules, packages, virtual environments, uv 🧠

**Learn (15 min)**
- A **module** is a `.py` file. A **package** is a folder of modules (traditionally with an `__init__.py`).
- `import x` runs the whole file `x.py` once. `if __name__ == "__main__":` code only runs when the file is executed directly.
- A **virtual environment** gives each project its own isolated set of dependency versions.
- **uv** manages Python versions, dependencies (`pyproject.toml`) and the lock file (`uv.lock`) in one tool.
  - `uv init`, `uv add <pkg>`, `uv add --dev pytest`, `uv run python file.py`
- Docs: https://docs.astral.sh/uv/guides/projects/

**Do (35 min)**
1. In this repo, run `uv init` (if there's no `pyproject.toml` yet), then `uv add --dev pytest ruff`.
2. Create a package `src/toolkit/` with `__init__.py` and `orders.py`. Move your best versions of `parse_order_value`, `calculate_customer_totals` and `clean_orders` (Day 13) into it.
3. Import them in `src/day15/exercises15.py`: `from toolkit.orders import clean_orders`. If the import fails, you've hit `sys.path`. Read the error, and ask Claude for a *hint* (not the answer) about how Python finds packages.
4. Add some top-level `print("loaded!")` to `orders.py`, import it, and see that it runs on import. Move the demo code under `if __name__ == "__main__":`.
5. Run `uv run ruff check .` and `uv run ruff format .`. Read what each fix means.

**Check yourself**
1. What does `if __name__ == "__main__":` protect against?
2. Why use a virtual environment instead of installing globally?
3. What's the difference between `pyproject.toml` and `uv.lock`?
4. What's a circular import, and how do you fix it?

<details><summary>Answers</summary>

1. It stops demo or script code from running when another file imports the module.
2. Different projects need different library versions. Isolating them avoids conflicts and makes setups reproducible.
3. `pyproject.toml` declares what you need (often as ranges, e.g. `requests>=2.31`). The lock file pins the **exact** resolved versions, so every machine and CI run installs the same thing.
4. Module A imports B and B imports A, so one of them is only half-loaded when it's used. Fix it by moving the shared code into a third module, or by restructuring the dependencies.
</details>

---

## Day 16 — Exceptions done right and logging 🧠

**Learn (15 min)**
- Catch **specific** exceptions. Never write `except Exception: pass`.
- Custom exceptions: `class InvalidOrderError(ValueError): ...`
- `raise NewError("context") from e` keeps the original cause in the traceback.
- `logging`: `logger = logging.getLogger(__name__)`. Levels: DEBUG < INFO < WARNING < ERROR < CRITICAL.
- `logger.exception("msg")` inside an `except` block logs the traceback too.
- Docs: https://docs.python.org/3/howto/logging.html

**Do (35 min)** in `src/toolkit/` and `src/day16/`
1. Create `toolkit/errors.py` with `class InvalidOrderError(ValueError)` that stores an `order_id` attribute.
2. Write a `parse_order(raw: dict) -> dict` that **raises** `InvalidOrderError` on bad data, instead of returning `None`.
3. Write a `process(raw_orders)` that catches `InvalidOrderError` **per row**, logs a WARNING with the order_id, collects rejects into a list, and returns `(valid, rejected)`. Any other unexpected exception should crash.
4. Configure logging once in the entry script:
   `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")`
5. Wrap a `json.JSONDecodeError` in `raise ConfigError("bad config file") from e` and read the full traceback.

**Check yourself**
1. Why is `except Exception: pass` especially bad in data pipelines?
2. When should a pipeline skip and quarantine a bad row, and when should the whole run fail?
3. What's the difference between `logger.error` and `logger.exception`?
4. Why use `logging` instead of `print`?

<details><summary>Answers</summary>

1. It hides bugs and causes **silent data loss**. Reports end up wrong and nobody knows.
2. Skip and quarantine for **expected, row-level** problems (one malformed record). Fail for **systemic** problems: the source is down, the schema changed, too many rows were rejected (e.g. more than 5%), or config is missing. A good pipeline does both, and alerts when the reject rate is high.
3. `exception` logs at ERROR level **plus the traceback**. Use it inside `except` blocks.
4. Levels, timestamps and module names, and logs can be routed to files or monitoring tools. Verbosity can be changed through config without touching the code.
</details>

---

## Day 17 — Testing with pytest 🧠

**Learn (10 min)**
- Test files are named `tests/test_*.py`, and test functions `def test_*():`. Use plain `assert`.
- `@pytest.mark.parametrize` runs one test with many inputs.
- **Fixtures** (`@pytest.fixture`) provide reusable setup, injected by argument name.
- `tmp_path` is a built-in fixture that gives each test a fresh temporary folder.
- `with pytest.raises(InvalidOrderError):`
- Docs: https://docs.pytest.org/en/stable/getting-started.html

**Do (35 min)** in `tests/test_orders.py`
1. Tests for `calculate_customer_totals`: normal input, empty list, a customer with one order.
2. Parametrize `parse_order_value` with ≥ 6 cases: `"10"`, `"10.5"`, `" 7 "`, `"abc"`, `""`, `None`. Did `None` surprise you? Fix the function if needed (Day 8 only catches `ValueError`…).
3. Test that `parse_order` raises `InvalidOrderError` on a bad value.
4. Create a `sample_orders` fixture and use it in 2 tests.
5. Test a function that writes a CSV, using `tmp_path`. Read the file back and assert on its contents.
6. Run `uv run pytest -v`. Break a function on purpose, then read the failure output.

**Check yourself**
1. What's a fixture?
2. Why are edge-case tests (empty, `None`, wrong types) especially important in data engineering?
3. Unit test vs integration test?
4. Why test with `tmp_path` instead of real project folders?

<details><summary>Answers</summary>

1. A function that provides setup data or resources to tests, injected by parameter name, and reusable across tests.
2. Real data is dirty. A crash is visible, but a **silently wrong number** in a report is worse.
3. A unit test checks one function in isolation (fast, no I/O). An integration test checks that several parts work together (e.g. API → file → database).
4. Isolation. Tests don't depend on or damage real files, and each test starts clean.
</details>

---

## Day 18 — AI-assisted development + Week 2 review 🤖🔁

**Learn (10 min)**
- LLM coding assistants predict likely code. They're often right, sometimes subtly wrong, and always confident.
- Your job moves from "typing code" to **specifying, reviewing and verifying**, which is exactly what senior engineers do.
- Never share secrets, credentials, personal data or proprietary code with tools your company hasn't approved.

**Do (35 min)**
1. Ask Claude to review your `toolkit` package:
   > "Act as a senior data engineer reviewing a PR. List the top 5 issues in this code by severity (correctness > robustness > readability). Explain why each matters. Don't rewrite the code."
2. In `src/day18/REVIEW_NOTES.md`, write **accept / reject + one sentence why** for each point. Disagreeing with a good reason is a senior skill.
3. Ask Claude to propose 5 extra edge-case tests. Add them and run them. Did any find a real bug? Was any test itself **wrong**?
4. Commit.

**Weekly quiz**
1. An AI-generated test passes. Does that prove your function is correct?
2. Name 3 things that should never go into a prompt for a public AI tool.
3. Why should `summarize()` not read files itself?
4. What does `raise X from e` give you in the traceback?
5. Your pipeline rejected 40% of rows today, up from 0.5% usually. Should it succeed?

<details><summary>Answers</summary>

1. No. The test may encode the same wrong assumption as the code. You still need to check that the *expectation* is correct.
2. Passwords, API keys and tokens; customer personal data (PII); confidential company code and data.
3. Separating I/O from logic makes the logic pure, so it's testable without files and reusable with any source.
4. Both errors, linked with "The above exception was the direct cause of…", so you see the root cause and the context.
5. Probably not. A sudden jump in the reject rate usually means a source or schema change. Fail, or at least alert, above a threshold.
</details>

📝 Confidence log.

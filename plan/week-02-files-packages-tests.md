# Week 2 · Files, packages, errors, logging, tests

**Phase 1 — Python that pipelines are made of** · Days 14–18
[← Week 1](week-01-pythonic-data.md) · [Plan overview](README.md) · [Week 3 →](week-03-rest-apis.md)

> **This week's outcome:** you read and write the file formats pipelines live on, structure code as a real package, fail loudly with useful errors and logs, and prove it works with pytest.
>
> **Project milestone:** `shopflow/` exists. Its first connector lands local order files in the raw layer, with metadata and tests.

| Day | Topic | Time |
|---|---|---|
| 14 | `pathlib` + CSV, JSON and JSONL | ~45 min |
| 15 | uv project and package layout: create `shopflow/` | ~50 min |
| 16 | Exceptions done right + `logging` | ~45 min |
| 17 | pytest: fixtures, parametrize, `tmp_path` | ~50 min |
| 18 | 🛠 Build day: first source, local order files → raw + quiz | ~60 min |

---

<a id="day-14"></a>
## Day 14 · `pathlib` + CSV, JSON and JSONL

⏱ ~45 min · 📁 `src/day14/exercises14.py`

> 🎯 **By the end you can:** read and write CSV, JSON and JSONL safely, with paths that work on any OS.
> 💼 **At work:** most "new source" tickets start with "they'll drop a file for us". Encodings and line endings are where they break.

### 📖 Learn (15 min)
- `from pathlib import Path`. Join with `/`: `Path("data") / "raw" / "orders.json"`. Use `.exists()`, `.suffix`, `.stem`, `.glob("*.csv")`, `.mkdir(parents=True, exist_ok=True)`.
- **Always pass `encoding="utf-8"`.** On Windows the default may be `cp1252`, so Polish letters break silently.
- CSV: open with `newline=""`, otherwise the `csv` module writes blank lines between rows on Windows. `csv.DictReader` gives one dict per row, and **every value is a string**.
- JSON is one document. **JSONL** (JSON Lines) is one JSON object per line, so you can stream it and append to it. It's the most common raw format.
- Docs: https://docs.python.org/3/library/pathlib.html · https://docs.python.org/3/library/csv.html

### 💻 Do (25 min)
- [ ] **1.** Build a `Path` to your Day 3 `src/day3/orders.json` relative to this file: `Path(__file__).parent.parent / "day3" / "orders.json"`. Print `.name`, `.suffix`, `.exists()`.
- [ ] **2.** Read `src/day3/orders.txt` (no header) with `csv.DictReader(f, fieldnames=["order_id", "value"])`. Print the type of `value`. Why is it a string?
- [ ] **3.** Write the same orders to `src/day14/out/orders.csv` with `csv.DictWriter` (header included), and to `orders.jsonl` with one `json.dumps(order)` per line. Read the JSONL back line by line.
- [ ] **4.** Write `{"customer": "Łukasz Żółć"}` to JSON twice: with default `json.dumps`, and with `ensure_ascii=False`. Open both files and compare.
- [ ] **5.** *Predict the output:* on Windows, write a CSV **without** `newline=""` and open it in Notepad or Excel. What do you see, and why?
- ⭐ *Stretch:* list every `.json` file under `src/` with `Path("src").rglob("*.json")`. Which of them are invalid JSON? (Hint: you have a `broken.json`.)

### ✅ Check yourself (5 min)
1. Why `Path("a") / "b"` instead of `"a" + "/" + "b"`?
2. What type does `csv.DictReader` give you for the number `120`?
3. Why do pipelines prefer JSONL over one big JSON array for raw data?
4. A supplier file shows `Å‚` instead of `ł`. What happened?

<details><summary>Answers</summary>

1. It handles separators on every OS, and gives you helpers (`.parent`, `.suffix`, `.mkdir`) instead of string hacking.
2. `str` (`"120"`). CSV has no types. You convert later, deliberately.
3. You can process it line by line without loading everything, append to it, and one bad line doesn't make the whole file unreadable.
4. A UTF-8 file was decoded with the wrong encoding (like cp1252). Read it with `encoding="utf-8"`.
</details>

---

<a id="day-15"></a>
## Day 15 · uv project and package layout: create `shopflow/`

⏱ ~50 min · 📁 `shopflow/` (repo root)

> 🎯 **By the end you can:** create a Python package with uv, import between its modules, and run it as a module or a command.
> 💼 **At work:** every real pipeline repo is a package with a `pyproject.toml`, not a folder of scripts.

### 📖 Learn (10 min)
- A **module** is a `.py` file. A **package** is a folder of modules with an `__init__.py`.
- The **src layout** (`src/shopflow/...`) forces you to import the *installed* package, so tests see what users see.
- `uv init --package` creates `pyproject.toml` and `src/<name>/__init__.py`. `uv add x` installs a dependency and records it. `uv run ...` runs inside the project's environment.
- `if __name__ == "__main__":` runs code only when the file is executed directly, not when it's imported.
- Use absolute imports inside the package: `from shopflow.raw import write_raw`.
- Docs: https://docs.astral.sh/uv/concepts/projects/init/

### 💻 Do (35 min)
- [ ] **1.** In PowerShell, from the repo root:
  ```powershell
  uv init --package --vcs none shopflow
  cd shopflow
  uv add --dev pytest ruff
  uv run shopflow          # runs main() from src/shopflow/__init__.py
  ```
- [ ] **2.** Create the layout from the [README](README.md#-the-project-youll-build-shopflow): `src/shopflow/sources/__init__.py` (empty), `tests/`, `data/`. In PowerShell: `New-Item -ItemType Directory src/shopflow/sources, tests, data`.
- [ ] **3.** Add `shopflow/.gitignore` with `data/` and `.venv/`. Run `git status` from the repo root and check that nothing in `data/` shows up.
- [ ] **4.** Create `src/shopflow/sources/local_files.py` with `def hello() -> str: return "local files"` and a `if __name__ == "__main__": print(hello())` block. Run it two ways: `uv run python -m shopflow.sources.local_files`, then import it from `uv run python` and call `hello()`. Notice that the print only happens once.
- [ ] **5.** *Explain why:* run `uv run python src/shopflow/sources/local_files.py` after adding `from shopflow import main` at the top. It works because the package is installed. Delete that import again.
- ⭐ *Stretch:* open `pyproject.toml` and find `[project.scripts]`. Add a second command, `shopflow-hello = "shopflow.sources.local_files:hello"`, and run it.

### ✅ Check yourself (5 min)
1. What's the difference between a module and a package?
2. What does `if __name__ == "__main__":` protect against?
3. Why use the src layout instead of putting `shopflow/` at the top?
4. Why is `data/` gitignored, and where does real data live instead?

<details><summary>Answers</summary>

1. A module is one `.py` file. A package is a folder of modules (with `__init__.py`) that you import by name.
2. Code running as a side effect of `import`. Without it, importing a module for a test would start the pipeline.
3. With the package at the top, `import shopflow` picks up the local folder even if packaging is broken. The src layout makes tests use the installed package, so packaging bugs show up early.
4. Data is big, changes often and may be sensitive. Git is for code. Data lives in storage (a disk, S3, a warehouse).
</details>

---

<a id="day-16"></a>
## Day 16 · Exceptions done right + `logging`

⏱ ~45 min · 📁 `src/day16/exercises16.py`

> 🎯 **By the end you can:** raise clear custom errors, keep the original cause, and log instead of print.
> 💼 **At work:** at 3 a.m. the log is all you have. "Something went wrong" helps nobody. "Order 17: value 'abc' is not a number (file orders_2026-11-03.csv)" does.

### 📖 Learn (15 min)
- Catch **specific** exceptions (`except ValueError`), never a bare `except:`. Don't swallow errors with `pass`.
- Custom exceptions: `class ShopflowError(Exception): ...` then `class SourceError(ShopflowError): ...`. Callers can catch the whole family.
- `raise SourceError("...") from e` keeps the original traceback ("The above exception was the direct cause…").
- `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")` once, at the entry point. In each module: `log = logging.getLogger(__name__)`.
- `log.info("Loaded %d rows", n)` (lazy formatting). Inside `except`, `log.exception("...")` also logs the traceback.
- Docs: https://docs.python.org/3/howto/logging.html

### 💻 Do (25 min)
- [ ] **1.** Write `parse_value(raw: str) -> float` that raises `InvalidRecordError(f"value {raw!r} is not a number")` **from** the original `ValueError`. Call it with `"abc"` and read the full traceback.
- [ ] **2.** Rewrite your Day 3 `broken.json` reader so it raises `SourceError(f"cannot parse {path}")` from `json.JSONDecodeError`, instead of printing.
- [ ] **3.** Process `["120", "80", "abc", "", "45.5"]`: log a WARNING for each bad value (with its index), INFO for the total, and **continue**. Use a logger, not `print`.
- [ ] **4.** *Bug hunt:* what's wrong here? List three problems.
  ```python
  try:
      orders = json.load(open(path))
      total = sum(o["value"] for o in orders)
  except:
      print("error")
      total = 0
  ```
- ⭐ *Stretch:* add a `logging.FileHandler("pipeline.log", encoding="utf-8")` next to the console handler, with the file at DEBUG level and the console at INFO.

### ✅ Check yourself (5 min)
1. What does `raise X from e` add compared to just `raise X`?
2. When is it OK to catch an exception and continue?
3. Why `log.info("rows=%d", n)` instead of `print(f"rows={n}")` in a pipeline?
4. Which is worse in production: a pipeline that crashes, or one that silently writes 0 rows? Why?

<details><summary>Answers</summary>

1. It records the original exception as the cause, so the traceback shows both the low-level error and your context.
2. When you handle it deliberately: log it, count or quarantine the bad record, and the business accepts that. Never "just in case".
3. Logs have levels, timestamps and module names, can go to files or monitoring tools, and can be turned up or down without code changes.
4. The silent one. A crash gets noticed and fixed. Zero rows can flow into reports for weeks before anyone asks.
</details>

---

<a id="day-17"></a>
## Day 17 · pytest: fixtures, parametrize, `tmp_path`

⏱ ~50 min · 📁 `shopflow/tests/test_basics.py`

> 🎯 **By the end you can:** write fast tests for pure functions and file code, with fixtures and parametrized cases.
> 💼 **At work:** tests let you change a pipeline without fear. Reviewers look for them first.

### 📖 Learn (15 min)
- Test files are `test_*.py`, test functions are `test_*`. Plain `assert` is enough. Run with `uv run pytest -v`.
- `with pytest.raises(InvalidRecordError, match="not a number"):` checks that an error is raised.
- `@pytest.mark.parametrize("raw, expected", [("120", 120.0), ("45.5", 45.5)])` runs one test for many cases.
- A **fixture** is a function marked `@pytest.fixture` that prepares data. Tests request it by naming it as a parameter. Shared fixtures go in `tests/conftest.py`.
- `tmp_path` is a built-in fixture: a fresh temporary folder per test. Use it instead of writing to real paths.
- Docs: https://docs.pytest.org/en/stable/how-to/fixtures.html

### 💻 Do (30 min)
- [ ] **1.** Copy `parse_value` and `InvalidRecordError` from Day 16 into `src/shopflow/errors.py` and `src/shopflow/parsing.py`. Test it with `parametrize`: `"120"`, `"45.5"`, `" 80 "`, and a `pytest.raises` test for `"abc"` and `""`.
- [ ] **2.** In `tests/conftest.py`, add a `sample_orders` fixture that returns the 4 orders from `src/day3/orders.json`. Write a test for a pure `total_by_customer(orders)` function (expected: `{"Anna": 370, "John": 80, "Mark": 50}`).
- [ ] **3.** Use `tmp_path` to test a JSONL round trip: write `sample_orders` to `tmp_path / "orders.jsonl"`, read it back, and assert they're equal.
- [ ] **4.** Break `total_by_customer` on purpose and read pytest's failure output. Then fix it.
- [ ] **5.** 📘 Fill in **§6 Test and check quality** in your [playbook](new-source-playbook.md#6--test-and-check-quality): what you'd always test in a new source's parsing code.
- ⭐ *Stretch:* run `uv add --dev pytest-cov` and then `uv run pytest --cov=shopflow`. Which lines aren't covered?

### ✅ Check yourself (5 min)
1. What does a fixture give you that a module-level variable doesn't?
2. Why test pure functions first?
3. Why must tests never write to `data/`?
4. A test passes locally and fails in CI. Name two likely causes.

<details><summary>Answers</summary>

1. A fresh copy per test (so tests can't affect each other), setup and teardown, and reuse via `conftest.py`.
2. No files, network or mocks are needed, so the tests are fast, simple and reliable, and they cover the logic that matters most.
3. They'd depend on, or damage, whatever is there. `tmp_path` keeps each test isolated and repeatable.
4. Hidden dependencies on your machine: local files or env vars, the current working directory, time zone or date, encoding defaults, or test order.
</details>

---

<a id="day-18"></a>
## Day 18 · 🛠 Build day: first source, local order files → raw + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/sources/local_files.py`

> 🎯 **By the end you can:** land files from a drop folder in a dated raw layer, with metadata, logging and tests.
> 💼 **At work:** "the partner uploads a file every night" is the most common integration there is.

### 💻 Do (40 min)
- [ ] **1.** Copy `src/day3/orders.json` and `src/day3/orders.txt` (rename it `orders.csv`) into `shopflow/data/landing/orders/` and into `shopflow/tests/fixtures/`.
- [ ] **2.** In `local_files.py`, write `read_orders(path: Path) -> list[dict]`. It picks the reader by `path.suffix`: `.json` → `json.load`, `.csv` → `DictReader` with `fieldnames=["order_id", "value"]`. Unknown suffix → raise `SourceError`.
- [ ] **3.** Write `land_file(src: Path, *, base_dir: Path, load_date: date) -> Path`. It copies the file **unchanged** (`shutil.copy2`) to `base_dir / "raw/local_files/orders" / f"load_date={load_date:%Y-%m-%d}" / src.name`, and writes `_metadata.json` next to it:
  ```json
  {"source": "local_files", "entity": "orders", "file": "orders.json",
   "row_count": 4, "size_bytes": 312, "extracted_at": "2026-11-03T07:00:00+00:00"}
  ```
  Use `datetime.now(timezone.utc).isoformat()` for `extracted_at`.
- [ ] **4.** Add `main()` with logging: land every file in `data/landing/orders/`, log one INFO line per file and a WARNING if a file has 0 rows. Run it: `uv run python -m shopflow.sources.local_files`.
- [ ] **5.** Tests in `tests/test_local_files.py` (use `tmp_path` as `base_dir`): both readers return 4 rows; the landed file is byte-identical to the source; metadata has the right `row_count`; an unknown suffix raises `SourceError`.
- [ ] **6.** Run the job twice for the same date. Is the result the same? Write one sentence in your code explaining why (that's *idempotency*, more in Week 6).

### ✅ Weekly quiz
1. Why do we copy the file unchanged into raw instead of the cleaned rows?
2. What's `newline=""` for in `open()` with the `csv` module?
3. Explain out loud, as in an interview: "How do you structure error handling in a pipeline?"
4. What does `tmp_path` give you, and why does it matter for file code?
5. `uv run python -m shopflow.sources.local_files` vs `uv run python src/shopflow/sources/local_files.py`: which is better for code inside a package, and why?

<details><summary>Answers</summary>

1. Raw is your record of what the source actually sent. If the cleaning logic has a bug, you can fix it and reprocess. You can't if you only kept the cleaned version.
2. It stops Python translating line endings, so the `csv` module controls them. Without it you get blank rows on Windows and broken multi-line fields.
3. Fail fast on unexpected errors, with custom exceptions that add context (`raise ... from e`). Handle expected, record-level problems deliberately: log them and quarantine the record. Never swallow errors. Log at the entry point with levels, and alert on failures and on suspicious results like 0 rows.
4. A new empty folder for each test, cleaned up automatically. Tests stay isolated, repeatable and safe for real data.
5. `-m`. It runs the module as part of the package, so absolute imports and `__name__` behave the same way they do everywhere else.
</details>

📘 Before you close: add the "file drop" gotchas you hit today (encoding, header, empty files) to **§2 Extract** in your [playbook](new-source-playbook.md#2--extract).

---

## 🏁 End of week 2: I can…
- [ ] Read and write CSV, JSON and JSONL with the right encoding and `newline` settings
- [ ] Create a uv package with the src layout and run its modules with `-m`
- [ ] Raise custom exceptions with `from e`, and log instead of print
- [ ] Write pytest tests with fixtures, `parametrize` and `tmp_path`
- [ ] Land a file in a dated raw partition with metadata

📈 Rate your confidence for Week 2 in the [progress tracker](README.md#-progress-tracker).

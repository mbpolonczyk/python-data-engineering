# Python for Data Engineering — 12-Week Plan

> **Goal:** be confident integrating **any new data source**, writing **clean ETL transformations**, and doing it at scale with **PySpark**, all in production-quality Python.

⏱ 30–60 min a day · 5 days a week · weekends optional (catch up or rest)
📍 Day numbers continue from your exercises (days 1–8 ✅). The plan starts at **Day 9**.

---

## ▶ Where am I?

**Next up: [Day 9 · Counter and defaultdict](week-01-pythonic-data.md#day-9)**

*(Update this line when you finish a day, so opening this file always tells you what to do next.)*

---

## 🗺 The roadmap

| Phase | Weeks | You'll be able to… |
|---|---|---|
| **1 · Python that pipelines are made of** | 1–2 | Write clean, tested Python for working with data |
| **2 · Integrating new data sources** | 3–5 | Pull data from APIs, databases, files and object storage reliably, and validate it |
| **3 · ETL transformations** | 6–7 | Transform data with SQL and DataFrames, load it idempotently, check its quality |
| **4 · PySpark** | 8–10 | Build, test and tune Spark jobs, with incremental loads into Delta Lake |
| **5 · Production & proof** | 11–12 | Ship a configurable, tested and containerised pipeline, then integrate a brand-new source on your own |

| Week | Topic | Days |
|---|---|---|
| 1 | [Pythonic data handling](week-01-pythonic-data.md) | 9–13 |
| 2 | [Files, packages, errors, logging, tests](week-02-files-packages-tests.md) | 14–18 |
| 3 | [Source #1: REST APIs](week-03-rest-apis.md) | 19–23 |
| 4 | [Databases, files and object storage as sources](week-04-more-sources.md) | 24–28 |
| 5 | [Data contracts and validation](week-05-validation.md) | 29–33 |
| 6 | [SQL transformations and loading with DuckDB](week-06-sql-duckdb.md) | 34–38 |
| 7 | [DataFrames and data quality](week-07-dataframes-quality.md) | 39–43 |
| 8 | [PySpark fundamentals](week-08-pyspark-fundamentals.md) | 44–48 |
| 9 | [PySpark transformations and testing](week-09-pyspark-transformations.md) | 49–53 |
| 10 | [PySpark performance and Delta Lake](week-10-pyspark-performance-delta.md) | 54–58 |
| 11 | [Production-ready ETL](week-11-production.md) | 59–63 |
| 12 | [Final challenge: integrate a new source on your own](week-12-final-challenge.md) | 64–68 |

---

## 🧩 How a day works

Each day is one card with the same shape:

1. 🎯 **By the end you can…**: what you'll be able to do today.
2. 📖 **Learn** (10–15 min): short notes and a docs link. Type the examples yourself.
3. 💻 **Do** (20–35 min): tick tasks off as you finish them. Write your own attempt **before** asking AI.
4. ✅ **Check yourself** (5 min): answer out loud, then open the hidden answers.
5. `git commit` and update **▶ Where am I?** above.

Day 5 of every week is a **🛠 build day**: you add a feature to your project, take a short quiz, and rate your confidence.

Only have 30 minutes? Do Learn and the first two tasks. ⭐ Stretch tasks are optional.

---

## 🛠 The project you'll build: `shopflow`

You'll build one e-commerce data pipeline across the whole plan. Each week it gets a new piece, so by Week 12 you have a working pipeline you understand completely.

```
 SOURCES                         RAW          STAGING         MARTS
 ───────                         ───          ───────         ─────
 Local order files  (wk 2)  ┐
 DummyJSON REST API (wk 3)  │    JSON/CSV     validated,      daily revenue,
 SQLite "ERP" DB    (wk 4)  ├──► as received ─► typed, ──────► customer stats,
 Supplier Excel     (wk 4)  │    + metadata    deduped        product perf.
 S3 clickstream     (wk 4)  ┘                  (DuckDB → PySpark → Delta)
 NBP exchange rates (wk 12, on your own)
```

It lives in `shopflow/` at the root of this repo and is created on Day 15:

```
shopflow/
  pyproject.toml
  src/shopflow/
    sources/      one module per data source (a "connector")
    raw.py        writes the raw layer
    validate/     pydantic models, quarantine
    transform/    SQL / pandas / polars transformations
    spark/        PySpark jobs (from Week 8)
    cli.py
  tests/
  data/           gitignored: raw/, validated/, quarantine/, staging/, marts/
```

Short practice exercises still go in `src/dayN/` as before.

### 📘 Your new-source playbook

[new-source-playbook.md](new-source-playbook.md) is a checklist **you** fill in as you learn. It covers how to evaluate, extract, validate, load and monitor any new data source. In Week 12 you'll use it, and only it, to integrate a source you've never seen. That's the moment you'll know you're confident.

---

## 📈 Progress tracker

Tick off days as you go. On each build day, rate your confidence from 1 to 5 and write down what still feels shaky. Come back to this table in Week 12.

| Week | Days | Confidence (1–5) | Still shaky |
|---|---|---|---|
| 1 | [ ] 9 [ ] 10 [ ] 11 [ ] 12 [ ] 13 | | |
| 2 | [ ] 14 [ ] 15 [ ] 16 [ ] 17 [ ] 18 | | |
| 3 | [ ] 19 [ ] 20 [ ] 21 [ ] 22 [ ] 23 | | |
| 4 | [ ] 24 [ ] 25 [ ] 26 [ ] 27 [ ] 28 | | |
| 5 | [ ] 29 [ ] 30 [ ] 31 [ ] 32 [ ] 33 | | |
| 6 | [ ] 34 [ ] 35 [ ] 36 [ ] 37 [ ] 38 | | |
| 7 | [ ] 39 [ ] 40 [ ] 41 [ ] 42 [ ] 43 | | |
| 8 | [ ] 44 [ ] 45 [ ] 46 [ ] 47 [ ] 48 | | |
| 9 | [ ] 49 [ ] 50 [ ] 51 [ ] 52 [ ] 53 | | |
| 10 | [ ] 54 [ ] 55 [ ] 56 [ ] 57 [ ] 58 | | |
| 11 | [ ] 59 [ ] 60 [ ] 61 [ ] 62 [ ] 63 | | |
| 12 | [ ] 64 [ ] 65 [ ] 66 [ ] 67 [ ] 68 | | |

### Skills checklist: your actual goal

Tick each one when you could do it **without looking anything up**. Most of these are covered by one or two weeks.

**Python for data**
- [ ] Group, count and dedupe data with the right data structure, and explain its Big-O (wk 1)
- [ ] Structure code as a package with logging, error handling and pytest tests (wk 2)
- [ ] Use generators, decorators and context managers in pipeline code (wk 3–4)

**Integrating new data sources**
- [ ] Extract from a paginated, authenticated REST API with retries and rate limiting (wk 3)
- [ ] Extract incrementally from a database using a watermark (wk 4)
- [ ] Read messy files (Excel, odd CSVs, encodings) and object storage (S3) (wk 4)
- [ ] Define a data contract, validate records, quarantine bad ones, detect schema drift (wk 5)

**ETL transformations**
- [ ] Build raw → staging → marts with SQL, including window functions and dedupe (wk 6)
- [ ] Load idempotently so reruns don't duplicate data (wk 6)
- [ ] Transform with pandas and polars, and avoid their classic pitfalls (wk 7)
- [ ] Write data-quality checks that stop a bad load (wk 7)

**PySpark**
- [ ] Explain driver, executors, partitions, lazy evaluation and actions (wk 8)
- [ ] Read files with explicit schemas and handle corrupt records (wk 8)
- [ ] Do joins, windows and aggregations in Spark, and test them with pytest (wk 9)
- [ ] Read a query plan, fix a shuffle-heavy or skewed job, and pick a partitioning (wk 10)
- [ ] Do incremental upserts with Delta Lake `MERGE` (wk 10)

**Production**
- [ ] Handle config and secrets properly, run backfills from a CLI, keep incremental state (wk 11)
- [ ] Run the pipeline in Docker with CI checks (wk 11)
- [ ] Integrate a brand-new source end to end using only your playbook (wk 12)

---

## 🤖 Using AI as a tutor (without letting it learn *for* you)

1. **Write your own attempt first.** Even if it's ugly or broken.
2. **Ask for hints, not solutions:** "Don't give me code. What concept am I missing?"
3. **Ask for a review:** "Review this like a senior data engineer. List the top 5 issues by severity. Don't rewrite it."
4. **Verify everything.** Run it and test it. AI is sometimes confidently wrong.
5. **Never paste secrets, credentials, customer data or company code** into AI tools your company hasn't approved.

In Claude Code, just say: **"Check my day 15 work and quiz me."**

---

## ⚙️ Setup (once)

- **Python 3.12+**. Check with `python --version`.
- **uv**, a fast package and project manager: `pip install uv`, or see https://docs.astral.sh/uv/
- **VS Code extensions**: Python, Ruff, Jupyter
- **For Week 8 (PySpark):** Java 17 plus WSL2, **or** Docker, **or** a free Databricks account. Day 44 walks you through the options. You don't need to install anything now.

## 📚 Optional reading

- *Fluent Python* (2nd ed.), Luciano Ramalho: dip into chapters as topics come up
- *Fundamentals of Data Engineering*, Joe Reis & Matt Housley: concepts and vocabulary
- *Learning Spark* (2nd ed.), Damji et al.: free PDF from Databricks, useful for weeks 8–10

## 🚀 After Week 12

- **Orchestration in depth**: Airflow or Dagster (you'll have seen the concepts in Week 11)
- **dbt**: SQL transformations as a product (you'll build a mini version in Week 6)
- **Cloud**: run `shopflow` on AWS, GCP or Azure, or on Databricks with a job schedule
- **Streaming**: Kafka plus Spark Structured Streaming
- **AI in pipelines**: LLM enrichment, embeddings, text-to-SQL

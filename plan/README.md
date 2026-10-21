# Python for Senior Data Engineering — 12-Week Plan

**Goal:** go from "I can write loops and functions" (days 1–8 ✅) to "I can design, build, test and explain a production-style data pipeline in Python, including AI features" — and have a public project to prove it.

**Time:** 30–60 min per session, 5 sessions per week (60 sessions in total). Weekends are optional and good for catching up.

Day numbers continue from your existing exercises, so the first new session is **Day 9** (`src/day9/`).

---

## How each session works

| Block | Time | What you do |
|---|---|---|
| **Learn** | 10–15 min | Read the concept notes and the linked docs. Type the small examples yourself. Don't copy-paste. |
| **Do** | 20–35 min | Exercises or a project step. Write the code **before** asking AI for help. |
| **Check** | 5–10 min | Answer the questions **out loud or in writing** before you open the answers. |
| **Commit** | 1 min | `git commit` with a clear message. Your commit history shows your progress. |

If you only have 30 minutes, do Learn plus the first two Do tasks, and finish the rest next time. Stretch tasks are optional.

### Tracks (mixed throughout the weeks)

- 🧠 **Fundamentals**: Python concepts, programming thinking, interview-style problems
- 🛠 **Project**: building **`shopflow`**, an e-commerce data pipeline (a separate GitHub repo you'll show employers)
- 🤖 **AI**: using LLMs inside pipelines, plus using AI tools as a professional engineer
- 🔁 **Review**: weekly consolidation, quizzes, and "I can now…" statements

---

## The 12 weeks at a glance

| Week | Theme | Days | You'll be able to… |
|---|---|---|---|
| 1 | [Pythonic data handling](week-01-pythonic-foundations.md) | 9–13 | Use `Counter`/`defaultdict`, reason about Big-O, avoid mutability bugs |
| 2 | [Code that lasts: files, modules, errors, tests](week-02-modules-errors-tests.md) | 14–18 | Structure code into packages, log properly, write pytest tests |
| 3 | [🛠 Project kickoff: Extract](week-03-project-extract.md) | 19–23 | Pull paginated data from an API with retries, save a raw layer |
| 4 | [Generators, decorators, context managers](week-04-intermediate-python.md) | 24–28 | Process data lazily, write your own `@retry` and `atomic_write` |
| 5 | [OOP, dataclasses, typing, validation](week-05-oop-typing-validation.md) | 29–33 | Model data with dataclasses/pydantic, quarantine bad records |
| 6 | [SQL & loading with DuckDB](week-06-sql-duckdb.md) | 34–38 | Do idempotent loads, use window functions, build marts, write Parquet |
| 7 | [DataFrames & data quality](week-07-dataframes-quality.md) | 39–43 | Use pandas and polars well, build data-quality checks |
| 8 | [Production-grade pipeline](week-08-production.md) | 44–48 | Handle config and secrets, build a CLI, do incremental loads and orchestration |
| 9 | [Concurrency & performance](week-09-concurrency-performance.md) | 49–53 | Use threads, processes and asyncio; profile and optimise code |
| 10 | [🤖 AI inside the pipeline](week-10-ai-in-pipeline.md) | 54–58 | Do LLM enrichment with structured output, caching, evals and embeddings |
| 11 | [🤖 AI interfaces + shipping](week-11-ai-interfaces-shipping.md) | 59–63 | Build text-to-SQL, use tool use and MCP, set up Docker and CI |
| 12 | [Senior polish & interview readiness](week-12-interview-readiness.md) | 64–68 | Explain trade-offs, handle system design, pass a timed coding round |

---

## Progress tracker

Tick these off as you go (`[ ]` → `[x]`). Ticking boxes every day helps you feel your progress.

**Week 1:** [  ] D9 [ ] D10 [ ] D11 [ ] D12 [ ] D13
**Week 2:** [ ] D14 [ ] D15 [ ] D16 [ ] D17 [ ] D18
**Week 3:** [ ] D19 [ ] D20 [ ] D21 [ ] D22 [ ] D23
**Week 4:** [ ] D24 [ ] D25 [ ] D26 [ ] D27 [ ] D28
**Week 5:** [ ] D29 [ ] D30 [ ] D31 [ ] D32 [ ] D33
**Week 6:** [ ] D34 [ ] D35 [ ] D36 [ ] D37 [ ] D38
**Week 7:** [ ] D39 [ ] D40 [ ] D41 [ ] D42 [ ] D43
**Week 8:** [ ] D44 [ ] D45 [ ] D46 [ ] D47 [ ] D48
**Week 9:** [ ] D49 [ ] D50 [ ] D51 [ ] D52 [ ] D53
**Week 10:** [ ] D54 [ ] D55 [ ] D56 [ ] D57 [ ] D58
**Week 11:** [ ] D59 [ ] D60 [ ] D61 [ ] D62 [ ] D63
**Week 12:** [ ] D64 [ ] D65 [ ] D66 [ ] D67 [ ] D68

### Confidence log

After each review day (D13, D18, D23, …), rate yourself from 1 to 5 on the week's topics and write one sentence about what still feels shaky. Revisit those sentences in Week 12. They'll show you how far you've come.

| Week | Confidence (1–5) | Still shaky |
|---|---|---|
| 1 | | |
| 2 | | |
| … | | |

---

## Using AI as a tutor (without letting it learn *for* you)

AI can make you much faster, but only if you still do the thinking yourself. Rules for this plan:

1. **Write your own attempt first.** Even if it's ugly or broken.
2. **Ask for hints, not solutions.** Example: "Don't give me the code. What concept am I missing?"
3. **Ask for review.** "Act as a senior data engineer reviewing a PR. List the top 5 issues by severity and explain why. Don't rewrite the code."
4. **Verify everything.** Run it, test it, and read the docs. AI is confidently wrong sometimes.
5. **Never paste secrets, credentials, customer data or company code** into AI tools that your company hasn't approved.

### Useful prompts

- *Quiz me:* "I just finished Day 24 (generators) from my plan. Ask me 5 questions one at a time, from easy to hard. Wait for my answer each time, grade it, and correct me."
- *Explain differently:* "Explain Python generators using an analogy from data engineering, then give me a 3-line example."
- *Interview drill:* "Ask me a senior data engineer interview question about idempotency. Then challenge my answer like a skeptical interviewer."
- *Code review:* "Review `src/day12/exercises12.py`. Focus on correctness, edge cases, and naming. Don't rewrite it."

In Claude Code you can just say: **"Check my day 15 work and quiz me."** Claude will read your files and ask you questions.

---

## Setup (once)

- Python **3.12+**. Check with `python --version`. `itertools.batched` (Day 25) needs 3.12.
- Install **uv**, a fast package and project manager: `pip install uv`, or see https://docs.astral.sh/uv/
- VS Code extensions: Python, Ruff, and optionally Even Better TOML
- A GitHub account (for the `shopflow` repo in Week 3)

## Recommended reading (optional, not required)

- *Fluent Python* (2nd ed.), Luciano Ramalho. The book for "advanced Python." Dip into chapters as topics come up.
- *Fundamentals of Data Engineering*, Joe Reis & Matt Housley. Concepts and vocabulary for senior interviews.
- Official docs: https://docs.python.org/3/tutorial/ and https://docs.python.org/3/library/

## After Week 12 (where to go next)

- **PySpark**: distributed processing (many senior jobs ask for it). Your pandas, polars and SQL skills transfer directly.
- **dbt**: SQL transformations as a product. You'll have built a mini version yourself in Week 6.
- **Cloud**: deploy `shopflow` to AWS, GCP or Azure (object storage + a scheduled container + a warehouse).
- **Streaming**: Kafka concepts, event-time vs processing-time.

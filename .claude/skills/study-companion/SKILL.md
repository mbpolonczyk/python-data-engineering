---
name: study-companion
description: Glossary notes and interview-style questioning for the Python/PySpark data-engineering study plan in this repo. Use when the user says "check day N", "save notes", "add X to my notes", "interview me", "interview me on <topic>", "quiz me", or when the daily lesson's quiz step needs questions (pick due items from notes/review-log.md). Writes term cards to notes/glossary/ and scores answers with spaced repetition in notes/review-log.md.
---

# Study companion

Three modes. Pick the one that matches the request; "check day N" runs **Save notes** after the code review from `CLAUDE.md`.

Files this skill owns (all committed to git, all English):

| File | Purpose |
|---|---|
| `notes/glossary/README.md` | Index: term → topic file → day learned |
| `notes/glossary/<topic>.md` | Term cards, grouped by topic (kebab-case file names, e.g. `collections.md`, `generators.md`, `pyspark-dataframe.md`) |
| `notes/review-log.md` | One row per term with score and next review date, plus a history of every question asked |

Today's date comes from the environment. Never put company code, credentials or customer data in any of these files.

---

## Mode 1 · Save notes

Trigger: "check day N", "save notes", "add X to my notes".

1. **Collect terms.** Read the day's card in `plan/`, the user's code in `src/dayN/`, and what was taught in this conversation. A term is any function, method, class, keyword, concept or gotcha the user met *for the first time* or clearly struggled with (e.g. `Counter.most_common`, `defaultdict`, generator expression, `KeyError`, in-place vs copy). Skip trivia the user clearly already knows (`print`, `len`).
2. **Check the index** (`notes/glossary/README.md`). If a card exists, **extend** it (add an example, gotcha or "Seen again: Day N") — never duplicate it.
3. **Write each new card** in the format from [references/card-template.md](references/card-template.md), into the right topic file. Create the topic file if needed, with a `# <Topic>` heading and a one-line description. Keep cards in the order they were learned.
4. **Update the index**: one row per term, sorted A–Z, linking to the card anchor.
5. **Add every new term to `notes/review-log.md`** with status `new`, interval `1` and next review = tomorrow. Terms the user missed in today's quiz get next review = tomorrow too.
6. **Report** in 2–4 lines: which cards were added or extended, with links. Don't paste the cards into chat.

Card rules: concise (10–15 lines), examples must run as written, and use e-commerce data (orders, SKUs, customers) where it fits. Definitions in plain words first, jargon second.

---

## Mode 2 · Interview me

Trigger: "interview me", "interview me on <topic/term>", "quiz me".

1. **Choose 5 questions.**
   - With a topic: questions about terms from that topic file.
   - Without a topic: first terms that are **due** (next review ≤ today, oldest first), then `miss`/`partial` terms, then recent terms. Mix in at least one term from an older week when possible.
   - Vary question types using [references/question-guide.md](references/question-guide.md). No two questions of the same type in a row.
2. **Ask one question at a time and wait** for the answer. Don't reveal the answer in the question.
3. **If the user says "I don't know"**: give one hint (name the concept or ask a guiding question) and let them try again. If still stuck, give the model answer and score it `miss`.
4. **After each answer**: give the score (`strong` / `partial` / `miss`), 1–3 lines of feedback (what was right, what was missing), and a short model answer phrased the way you'd say it in an interview. If the English was clumsy, add one more natural phrasing (max 1 line).
5. **Log it** right away in `notes/review-log.md` (see the scheduling rules below).
6. **At the end**: a summary line ("3 strong · 1 partial · 1 miss"), the terms coming back tomorrow, and one sentence on the pattern you noticed (e.g. "you know *what* it does but not *why it matters at scale*").

---

## Mode 3 · Spaced review (feeds the daily lesson quiz)

When `CLAUDE.md`'s daily lesson reaches the quiz step:

- Read `notes/review-log.md`. Of the 3 quiz questions, take **up to 2 from due terms** (oldest due first); the rest cover yesterday's material.
- Ask, score and log them exactly as in Mode 2.

### Scheduling rules (simple SM-2)

| Score | New interval | Streak |
|---|---|---|
| `miss` | 1 day | reset to 0 |
| `partial` | 3 days (or keep the current interval if it's already shorter) | unchanged |
| `strong` | max(7, current interval × 2), capped at 60 | +1 |

Next review = today + new interval. A term with streak ≥ 3 and an interval ≥ 30 is **solid**: mark it ✅ in the Status column and only ask it about once a month.

### `notes/review-log.md` format

The top table has one row per term, sorted by next review date (soonest first):

```markdown
| Term | Topic | Status | Last score | Streak | Interval | Next review |
|---|---|---|---|---|---|---|
| generator expression | [generators](glossary/generators.md#generator-expression) | 🔁 learning | miss | 0 | 1 | 2026-11-10 |
```

Status values: `🆕 new`, `🔁 learning`, `✅ solid`.

The **History** section underneath gets one appended line per question, newest at the bottom:

```markdown
- 2026-11-09 · generator expression · predict-output · miss · "didn't know"
```

Keep the history as a short paraphrase (≤ 12 words). Don't paste whole answers.

# Question guide

Write questions the way a data-engineering interviewer would ask them: short, concrete and connected to real data.

## Question types

| Type | Example |
|---|---|
| `define` | "In one or two sentences, what is a generator expression?" |
| `predict-output` | "What does this print? `c = Counter('banana'); print(c['z'], 'z' in c)`" |
| `spot-the-bug` | "`orders = orders.sort()`. What's wrong, and what's in `orders` now?" |
| `compare` | "`dict.get('x', 0)` vs `dd['x']` on a `defaultdict(int)`: what's the difference, and when does it cause a bug?" |
| `choose` | "You need the unique SKUs per customer. Which data structure would you use, and why?" |
| `scale` | "Your top-10-products script works on 10 MB. The file is now 50 GB. What changes?" |
| `sql-spark-twin` | "How would you write the same `defaultdict(float)` aggregation in SQL? And in PySpark?" |
| `write-it` | "Write a one-liner that counts orders per customer." (Only 1–3 lines of code. Typed answers are fine.) |

Rules:
- Ask about **one** term per question. A `compare` question counts as one term, and you log both terms.
- Use small, made-up e-commerce data, never real company data.
- Make questions harder as the streak grows: streak 0 → `define` / `predict-output`; streak 1–2 → `spot-the-bug` / `compare` / `choose`; streak 3+ → `scale` / `sql-spark-twin` / `write-it`.

## Scoring

| Score | Meaning |
|---|---|
| `strong` | Correct and complete. You could say it to an interviewer as is. Small wording slips are fine. |
| `partial` | The core idea is right, but a key part is missing (the *why*, the gotcha, the return value), or it needed a hint. |
| `miss` | Wrong, "I don't know", or right only after the model answer was shown. |

If you're unsure between two scores, give the lower one. A term that comes back sooner costs little.

## Feedback shape (after each answer)

```
**partial** · You got that it raises an error. The name of the error and how to avoid it were missing.
**Interview answer:** "It raises a KeyError. I'd use `.get(key, default)` or an `in` check, or a defaultdict if I'm building up values."
```

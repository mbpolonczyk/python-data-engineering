# Card template

Every glossary entry uses this shape. Headings are `###` so each one gets an anchor (`#counter`, `#generator-expression`) for links from the index and the review log.

````markdown
### `Counter.most_common(n)`
**What:** Returns the n most frequent items as `(item, count)` tuples, highest first.
```python
from collections import Counter
Counter(["drill", "saw", "drill"]).most_common(1)  # [('drill', 2)]
```
**Gotcha:** Leave out `n` and it returns *all* items, sorted.
**SQL/Spark twin:** `GROUP BY x ORDER BY COUNT(*) DESC LIMIT n` · `df.groupBy("x").count().orderBy(desc("count")).limit(n)`
**Interview line:** "For top-N I use `Counter.most_common`: one O(n) counting pass, no hand-written loop."
**Related:** [defaultdict](collections.md#defaultdict), [generator expression](generators.md#generator-expression)
_Learned: Day 9 · 2026-11-09_
````

## Field rules

| Field | Rule |
|---|---|
| Heading | The exact name as you'd type it in code (`dict.get`, `defaultdict`), or a plain concept name (Generator expression). |
| **What** | One sentence, in plain words. If you need two sentences, the second one says *why it exists*. |
| Code | 1–4 lines that run as written. Show the output in a comment. Use e-commerce data when it fits. |
| **Gotcha** | The mistake people actually make. Required. |
| **SQL/Spark twin** | Include it when one exists. Otherwise leave the line out. |
| **Interview line** | How you'd say it out loud in an interview, in 1 sentence. |
| **Related** | 1–3 links to other cards, in this file or another topic file. Leave the line out if there are none yet. |
| Footer | `_Learned: Day N · YYYY-MM-DD_`. When the term comes up again, append ` · Seen again: Day M`. |

Concept cards (not functions), such as *in-place vs copy* or *idempotency*, use the same fields. Their code shows the concept in action.

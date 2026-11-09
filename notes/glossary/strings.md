# Strings

Cleaning and splitting text. Strings are immutable: every method returns a **new** string.

### String cleaning: `.lower()`, `.replace()`, `.split()`
**What:** `.lower()` makes the text lowercase, `.replace(old, new)` swaps text (`new=""` deletes it), and `.split()` cuts the text at whitespace and returns a list. They can be chained.
```python
"Great Drill, great price!".lower().replace(",", "").replace("!", "").split()
# ['great', 'drill', 'great', 'price']
```
**Gotcha:** Strings never change in place, so `text.lower()` alone does nothing. You must use the result (`text = text.lower()`). A `.replace()` chain grows with every new punctuation mark, so prefer [`re.findall`](regex.md#refindall-and-w).
**SQL/Spark twin:** `LOWER()`, `REPLACE()`, `SPLIT()` · `F.lower`, `F.regexp_replace`, `F.split`
**Interview line:** "For a quick fix I chain `.lower().replace()`, but to split text into words I use a regex, so new punctuation doesn't break it."
**Related:** [`str.translate` + `string.punctuation`](#strtranslate-and-stringpunctuation), [`re.findall`](regex.md#refindall-and-w)
_Learned: Day 9 · 2026-11-09_

### `str.translate` and `string.punctuation`
**What:** `string.punctuation` is a ready-made string of every ASCII punctuation mark. Combined with `str.maketrans` + `.translate()`, it deletes all of them in one pass.
```python
import string
table = str.maketrans("", "", string.punctuation)   # "delete these characters"
"Bad?! Really... bad.".translate(table)             # 'Bad Really bad'
```
**Gotcha:** It only covers ASCII, so `„` `”` `…` `–` from real reviews are **not** removed.
**Interview line:** "To strip punctuation but keep one string I use `translate` with `string.punctuation`, knowing it misses non-ASCII quotes."
**Related:** [String cleaning](#string-cleaning-lower-replace-split)
_Learned: Day 9 · 2026-11-09_

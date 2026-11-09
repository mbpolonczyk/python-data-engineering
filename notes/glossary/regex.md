# Regex

Regular expressions (`import re`): patterns that describe text you want to find.

### `re.findall` and `\w+`
**What:** `re.findall(pattern, text)` returns a list of every piece of `text` that matches `pattern`. With `\w+` ("one or more word characters": letters, including Polish ones, digits and `_`), it **keeps the words** instead of removing punctuation one character at a time.
```python
import re
re.findall(r"\w+", "Bad?! Really... „great” 10/10".lower())   # ['bad', 'really', 'great', '10', '10']
re.findall(r"[\w']+", "Don't buy!".lower())                   # ["don't", 'buy']
```
**Gotcha:** `[ ]` means **one character** from the set. The `+` must go **after** `]`: `[\w']+`. If you write `[\w'+]` or `[\w']`, you get single letters. `\w+` alone splits `don't` into `['don', 't']`.
**SQL/Spark twin:** `F.split(F.regexp_replace(F.lower("text"), r"[^\w\s]", ""), r"\s+")`
**Interview line:** "To tokenise text I use an allow-list regex like `re.findall(r'\w+', text.lower())`, so I keep the words instead of chasing every punctuation mark."
**Related:** [String cleaning](strings.md#string-cleaning-lower-replace-split)
_Learned: Day 9 · 2026-11-09_

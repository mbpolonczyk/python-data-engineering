# Week 4 — Generators, itertools, decorators, context managers

These four topics are what most job ads mean by "advanced Python." Each one solves a real data engineering problem: processing data bigger than memory, batching, retrying, and safe file writes.

---

## Day 24 — Iterators and generators 🧠

**Learn (15 min)**
- **Iterable:** something you can loop over (list, file, dict). **Iterator:** the object that hands out items one by one, via `next()`. It raises `StopIteration` when it runs out.
- A **generator function** uses `yield`. It produces values lazily, one at a time, keeping almost nothing in memory.
- Generator expression: `(x * 2 for x in data)`. Same idea, inline.
- A generator can only be consumed **once**.

**Do (35 min)** in `src/day24/exercises24.py`
1. `it = iter([1, 2, 3])` → call `next(it)` 4 times. What happens on the 4th call?
2. Write `generate_fake_orders(n)` that **yields** `{"order_id": i, "customer": random.choice([...]), "value": round(random.uniform(5, 500), 2)}`.
3. Compute the total of 1,000,000 fake orders: (a) via a list, (b) via the generator. Compare peak memory with `tracemalloc`:
   ```python
   import tracemalloc
   tracemalloc.start(); ...; print(tracemalloc.get_traced_memory()); tracemalloc.stop()
   ```
4. Build a **generator pipeline**. Write 1M orders to a CSV, then:
   `read_rows(path)` → `parse(rows)` → `only_valid(rows)` → `sum(o["value"] for o in ...)`. Each step is a generator.
5. Consume a generator twice and see what you get the second time.

**Check yourself**
1. Iterable vs iterator?
2. `g = (x * 2 for x in range(3)); print(list(g)); print(list(g))` → ?
3. Why are generators key for large files?
4. When is a list better than a generator?

<details><summary>Answers</summary>

1. An iterable can give you an iterator (`iter(x)`). The iterator produces items with `next()` and remembers its position. A list is iterable, but it isn't an iterator.
2. `[0, 2, 4]` then `[]`. The generator is exhausted.
3. Memory stays constant, roughly one row at a time, however big the file is. You can stream data that's larger than RAM.
4. When you need to loop over the data several times, index into it, get `len()`, or sort it, and it fits in memory.
</details>

---

## Day 25 — `itertools` and batching 🧠

**Learn (10 min)**
- `itertools.islice(it, n)`: take the first n items from any iterator.
- `itertools.batched(it, n)` (3.12+): chunks of n.
- `itertools.chain(a, b)`: concatenate iterables lazily.
- `itertools.groupby(it, key)`: groups **consecutive** items that share a key.
- Docs: https://docs.python.org/3/library/itertools.html

**Do (30 min)** in `src/day25/exercises25.py`
1. Preview the first 5 fake orders from your 1M generator with `islice`.
2. Write your own `chunked(iterable, size)` generator using `islice`, then compare it with `itertools.batched`.
3. Use `chain` to combine the row generators of your three Day 14 CSV files into a single stream.
4. `groupby` orders by customer: first **without** sorting (see the wrong result), then sorted by customer. Compute totals per group.

**Check yourself**
1. Why does `itertools.groupby` need sorted input?
2. Why load into a database in batches of 1,000–10,000 rows instead of 1 row or all rows?
3. Can you do `my_generator[:5]`? What do you use instead?
4. What does `chain` save you compared with `list_a + list_b`?

<details><summary>Answers</summary>

1. It only groups *consecutive* equal keys. Unsorted input gives you the same key in several separate groups.
2. One row at a time means too many round trips, which is slow. All rows at once can run out of memory or hit a huge transaction. Batches balance speed and memory.
3. No, generators don't support slicing. Use `itertools.islice(gen, 5)`.
4. Memory. It doesn't build a new combined list, it just iterates one after the other.
</details>

---

## Day 26 — Decorators 🧠

**Learn (15 min)**
- Functions are objects: you can pass them around and return them.
- **Closure:** an inner function that remembers variables from the outer function.
- A **decorator** is a function that takes a function and returns a new function. `@timer` above `def f` is the same as `f = timer(f)`.
- Always use `@functools.wraps(func)` inside.
- A decorator **with arguments** (`@retry(times=3)`) needs one more layer: a function that returns a decorator.

**Do (35 min)** in `src/day26/exercises26.py`
1. `@timer`: logs `"<func name> took 0.123s"`.
2. `@log_calls`: logs the arguments and return value.
3. `@retry(max_attempts=3, exceptions=(ConnectionError,), base_delay=0.1)`. Test it on a function that fails twice and then succeeds (use a counter).
4. Print `my_func.__name__` with and without `functools.wraps`.

```python
import functools, time

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.3f}s")
        return result
    return wrapper
```

**Check yourself**
1. What is `@decorator` above `def f` equivalent to?
2. Why use `functools.wraps`?
3. What is a closure?
4. Why does `@retry(max_attempts=3)` need three nested functions?

<details><summary>Answers</summary>

1. `f = decorator(f)`
2. Without it, the wrapped function looks like it's called `wrapper` and loses its docstring. That breaks logs, debugging and some tools.
3. An inner function that keeps access to variables from the enclosing scope after the outer function has returned. `wrapper` remembers `func` this way.
4. `retry(3)` must *return a decorator*, which takes `func` and returns `wrapper`. So: arguments → decorator → wrapper.
</details>

---

## Day 27 — Context managers 🧠

**Learn (10 min)**
- `with` guarantees setup and cleanup, **even if an exception happens**.
- Class-based: `__enter__` / `__exit__(exc_type, exc, tb)`.
- Function-based: `@contextlib.contextmanager` with `yield` inside `try/finally`.

**Do (35 min)** in `src/day27/exercises27.py`
1. A `Timer` class context manager: `with Timer("load"): ...` prints the elapsed time.
2. The same thing as a `@contextmanager` function.
3. **`atomic_write(path)`**: yields a temporary file handle in the same folder, and on success calls `os.replace(tmp, path)`. On error it deletes the temp file and keeps the old file untouched.
   ```python
   with atomic_write(Path("summary.json")) as f:
       json.dump(summary, f)
   ```
4. Prove it: raise an exception halfway through writing and check that the original file is still intact.

**Check yourself**
1. What does `with` guarantee?
2. Why is atomic writing important in pipelines?
3. What happens if `__exit__` returns `True`?
4. In `@contextmanager`, why put `yield` inside `try/finally`?

<details><summary>Answers</summary>

1. The cleanup code (`__exit__`) runs however the block ends: normally, by `return`, or by an exception.
2. A crash halfway through a write leaves a **half-written file** that downstream jobs might read as if it were complete. Atomic rename means readers see either the old file or the new one, never a partial one.
3. The exception is **suppressed**. Usually you don't want that.
4. Otherwise an exception inside the `with` block skips your cleanup code.
</details>

---

## Day 28 — 🛠 Apply it to `shopflow`

**Do (40 min)**
1. Turn `fetch_all` into `iter_records(entity)`, a **generator** that yields records page by page.
2. Move your `@retry` decorator into `src/shopflow/utils.py` and use it on `fetch_page`. Delete the old retry loop. Your Day 22 tests should still pass. This is refactoring with a safety net.
3. Use `atomic_write` in `save_raw`.
4. Put `@timer` (or `with Timer(...)`) around each step and log the durations.
5. Commit: "Refactor extract to generators, retry decorator, atomic writes".

**Weekly quiz**
1. Your tests passed before and after the refactor. Why is that valuable?
2. Where in `shopflow` does laziness help, and where doesn't it?
3. Explain your `@retry` decorator line by line to an imaginary interviewer.
4. What problem does `atomic_write` solve that `try/except` alone doesn't?
5. Generator vs list for `iter_records`: what's the trade-off?

<details><summary>Answers</summary>

1. It proves the behaviour didn't change. Tests are what make refactoring safe.
2. It helps when streaming pages or rows into files and the database. It doesn't help when you need everything at once (sorting, or a `len` before processing).
3. (Your words.) Outer function takes the config → returns a decorator → which wraps `func` → `wrapper` loops over attempts, catches only the configured exceptions, sleeps with backoff, and re-raises after the last attempt.
4. `try/except` can handle the error, but the half-written file already exists on disk. Atomic rename means the target is never in a partial state.
5. A generator uses less memory and starts producing results sooner, but it's single-pass and you can't get `len` without consuming it.
</details>

📝 Confidence log.

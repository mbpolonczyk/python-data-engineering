# Week 5 · Data contracts and validation

**Phase 2 — Integrating new data sources** · Days 29–33
[← Week 4](week-04-more-sources.md) · [Plan overview](README.md) · [Week 6 →](week-06-sql-duckdb.md)

> **This week's outcome:** you describe every source entity with an explicit contract, and your pipeline rejects, quarantines and reports bad data instead of letting it leak downstream.
>
> **Project milestone:** `shopflow validate` turns every raw partition into a validated one, writes bad records to `data/quarantine/`, detects schema drift and fails the load when too many records are bad. **This ends Phase 2.**

| Day | Topic | Time |
|---|---|---|
| 29 | Classes, dataclasses, `Enum`: modelling records | ~45 min |
| 30 | Type hints and mypy on `shopflow` | ~45 min |
| 31 | pydantic v2 models as data contracts | ~50 min |
| 32 | Quarantine, schema drift, error-rate threshold | ~50 min |
| 33 | 🛠 Build day: a validate step for all sources + quiz | ~60 min |

---

<a id="day-29"></a>
## Day 29 · Classes, dataclasses and `Enum`: modelling records

⏱ ~45 min · 📁 `src/day29/exercises29.py`

> 🎯 **By the end you can:** model an order as typed objects instead of loose dicts, and explain when to use a plain class, a dataclass or an `Enum`.
> 💼 **At work:** `order["valeu"]` fails at 3 a.m. `order.valeu` fails in your editor.

### 📖 Learn (10 min)
- A **class** bundles data and behaviour. `__init__` sets attributes, `__repr__` controls how it prints.
- `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you. Use `field(default_factory=list)` for mutable defaults.
- `@dataclass(frozen=True)` makes instances immutable **and hashable**, so they can go into sets. Change one with `dataclasses.replace(obj, qty=2)`.
- `__post_init__` runs after `__init__`. It's a good place for simple checks.
- `class OrderStatus(StrEnum)` (Python 3.11+) is a fixed set of allowed values. `OrderStatus("paid")` looks up by value and raises `ValueError` for unknown ones.
- Docs: https://docs.python.org/3/library/dataclasses.html · https://docs.python.org/3/library/enum.html

### 💻 Do (30 min)
- [ ] **1.** Create `OrderStatus(StrEnum)` with `PENDING = "pending"`, `PAID`, `SHIPPED`, `CANCELLED`. Parse these raw values from your ERP source, normalizing with `.strip().lower()` first. Collect the ones that fail:
  ```python
  raw_statuses = ["paid", "SHIPPED", " pending", "lost", "cancelled"]
  ```
- [ ] **2.** `@dataclass(frozen=True) class OrderLine` with `product_id: int`, `unit_price: float`, `quantity: int` and a `line_total` property. In `__post_init__`, raise `ValueError` if `quantity <= 0`. Try `line.quantity = 5` and read the error.
- [ ] **3.** `@dataclass class Order` with `order_id`, `customer_id`, `status: OrderStatus`, `lines: list[OrderLine] = field(default_factory=list)` and a `total` property. Build one from this dict:
  ```python
  raw = {"order_id": 1001, "customer_id": 7, "status": "PAID",
         "lines": [{"product_id": 5, "unit_price": 19.99, "quantity": 2},
                   {"product_id": 9, "unit_price": 4.50, "quantity": 1}]}
  ```
  Expected `round(order.total, 2) == 44.48`.
- [ ] **4.** *Bug hunt:* write a plain `class Basket:` with `items = []` at **class** level and an `add(item)` method. Create two baskets, add to one, print both. Explain, then fix it.
- [ ] **5.** Put three `OrderLine`s (two identical) in a `set`. How many survive, and why does that work only because the class is frozen?
- ⭐ *Stretch:* add `slots=True` to `OrderLine`. Compare `sys.getsizeof` and try adding a new attribute.

### ✅ Check yourself (5 min)
1. What does `@dataclass` generate for you?
2. Why can a frozen dataclass go into a set, but a normal one can't?
3. Why is `status: OrderStatus` better than `status: str`?
4. Does a dataclass check that `quantity: int` really receives an int?

<details><summary>Answers</summary>

1. `__init__`, `__repr__` and `__eq__`. With options: ordering methods, `__hash__` (frozen) and `__slots__`.
2. Sets need hashable items. A normal dataclass defines `__eq__`, which sets `__hash__` to `None`. `frozen=True` makes it immutable, so a hash based on its fields is safe.
3. Typos and unknown statuses fail at the boundary, your editor autocompletes the values, and later code can `match` on a closed set.
4. No. Type hints aren't checked at runtime. `OrderLine(1, "abc", "2")` is accepted. That's exactly the gap pydantic fills on Day 31.
</details>

---

<a id="day-30"></a>
## Day 30 · Type hints and mypy on `shopflow`

⏱ ~45 min · 📁 `shopflow/` (`pyproject.toml`, `src/shopflow/sources/`)

> 🎯 **By the end you can:** type your connectors properly and let mypy find bugs before the pipeline runs.
> 💼 **At work:** types are documentation that can't go out of date, and CI rejects code that breaks them.

### 📖 Learn (10 min)
- `int | None` is the same as `Optional[int]`. Use `list[dict[str, Any]]`, `Iterator[dict]`, `Callable[[str], int]`.
- **Narrowing:** after `if x is None: return`, mypy knows `x` is not `None`.
- `TypedDict` describes the shape of a dict (good for raw JSON you don't convert). `NotRequired[...]` marks optional keys.
- `Protocol` (recap from Week 4): structural typing, "anything with these methods". Your `Connector` Protocol is checked by mypy, not at runtime.
- `Any` switches checking off. Keep it at the edges.
- Docs: https://mypy.readthedocs.io/en/stable/getting_started.html

### 💻 Do (30 min)
- [ ] **1.** In `shopflow/`: `uv add --dev mypy`. Add to `pyproject.toml`:
  ```toml
  [tool.mypy]
  python_version = "3.12"
  disallow_untyped_defs = true
  ```
  Run `uv run mypy src/` and note the error count.
- [ ] **2.** Add a `TypedDict` for a DummyJSON products page (`products: list[dict[str, Any]]`, `total`, `skip`, `limit`) and use it as the return type of your page-fetching function.
- [ ] **3.** *Predict, then run mypy:*
  ```python
  def latest_watermark(rows: list[dict[str, str]]) -> str | None:
      return max((r["updated_at"] for r in rows), default=None)

  wm = latest_watermark([])
  print(wm.startswith("2026"))
  ```
  What does mypy say? What happens at runtime? Fix it with narrowing.
- [ ] **4.** In a test, create a `FakeConnector` that is **missing** one method of your `Connector` Protocol and pass it to a function typed as `Connector`. Read mypy's message.
- [ ] **5.** Fix every mypy error in `src/`. Then try `uv run mypy --strict src/shopflow/sources/` on its own.
- ⭐ *Stretch:* add `uv run mypy src/` to the checks you run before every commit.

### ✅ Check yourself (5 min)
1. Is `Optional[int]` the same as "this argument is optional"?
2. `TypedDict`, dataclass or pydantic model: when do you use each?
3. `Protocol` vs abstract base class: what's the difference?
4. Your code passes mypy. Can it still crash on a bad API response?

<details><summary>Answers</summary>

1. No. It only means "an `int` or `None`". Whether you can leave the argument out depends on having a default value.
2. `TypedDict` for raw JSON you keep as dicts. Dataclass for internal objects you build yourself. pydantic at the boundary, where data comes from outside and must be checked at runtime.
3. A Protocol is structural: any class with matching methods fits, without inheriting. An ABC is nominal: you must subclass it, and it's enforced at runtime when you instantiate.
4. Yes. mypy checks your code, not the data. If the API sends `"price": null`, only a runtime check (pydantic, tomorrow) catches it.
</details>

---

<a id="day-31"></a>
## Day 31 · pydantic v2 models as data contracts

⏱ ~50 min · 📁 `src/day31/exercises31.py` → then `shopflow/src/shopflow/validate/models.py`

> 🎯 **By the end you can:** write a pydantic model per source entity that checks types and rules, maps source field names, and gives clear errors.
> 💼 **At work:** a **data contract** is the agreed shape and rules of data between a producer and you. The model is that contract in code.

### 📖 Learn (15 min)
- `class Product(BaseModel)`, `Field(gt=0, min_length=1)`, `Product.model_validate(d)`. Bad data raises `ValidationError`; `e.errors()` lists `loc`, `msg`, `type` and `input`.
- **Lax mode (default)** coerces: `"12.5"` → `12.5`, `"7"` → `7`. **Strict** rejects them. Per field: `Field(strict=True)`. Per model: `model_config = ConfigDict(strict=True)`.
- Gotcha: strict mode on a Python dict also rejects ISO date strings for `datetime`. Keep dates lax, or use `model_validate_json` on raw JSON lines.
- **Aliases** map source names to yours: `discount_pct: float = Field(alias="discountPercentage")`. Add `validate_by_name=True` to `ConfigDict` to accept both (pydantic 2.11+; older versions use `populate_by_name`).
- `extra="ignore"` (default) drops unknown fields, `"forbid"` rejects them, `"allow"` keeps them.
- `@field_validator("status", mode="before")` on a `@classmethod` cleans the value **before** type checks.
- Docs: https://docs.pydantic.dev/latest/concepts/models/ · https://docs.pydantic.dev/latest/concepts/strict_mode/

### 💻 Do (30 min)
- [ ] **1.** In `shopflow/`: `uv add pydantic`. Write `Product` with `id: int`, `title: str` (min length 1), `category: str`, `price: float` (> 0), `discount_pct` (alias `discountPercentage`, 0–100), `stock: int` (≥ 0), `rating: float | None = None`. Validate one real record from your Week 3 raw partition.
- [ ] **2.** *Predict, then run:* which of these pass in lax mode, and which in strict mode (`Product.model_validate(d, strict=True)`)?
  ```python
  a = {"id": "7", "title": "Drill", "category": "tools", "price": "19.99", "discountPercentage": 5, "stock": 3}
  b = {"id": 8, "title": "", "category": "tools", "price": 10, "discountPercentage": 120, "stock": -1}
  c = {"id": 9, "title": "Saw", "category": "tools", "price": 7.5, "discount_pct": 0, "stock": 1}
  ```
  For `b`, print `e.errors()` and count the errors. For `c`, make it pass without changing the data.
- [ ] **3.** `ErpOrder` for your SQLite source: `order_id: int = Field(strict=True)`, `customer_id: int`, `status: OrderStatus` (from Day 29), `amount: float`, `updated_at: datetime`. Add a `mode="before"` validator that turns `" PAID "` into `"paid"`. Adapt the field names to your Week 4 table.
- [ ] **4.** Nested contract: `CartItem` (`id`, `price`, `quantity` > 0) and `Cart` (`id`, `user_id` alias `userId`, `products: list[CartItem]`). Break the quantity of the second item and look at the error `loc`.
- [ ] **5.** `SupplierPrice` for the messy price list: a `mode="before"` validator turns `"12,50"` into `12.5` and an empty string into `None`.
- [ ] **6.** 📘 Playbook §4: write down lax vs strict, the alias trick, and one gotcha you hit.
- ⭐ *Stretch:* print `Product.model_json_schema()`. That JSON is a contract you could share with the source owner.

### ✅ Check yourself (5 min)
1. What's the difference between lax and strict mode, and when do you choose each?
2. Why use aliases instead of naming your fields `discountPercentage`?
3. `extra="ignore"` vs `extra="forbid"`: what's the trade-off for a source you don't control?
4. A validation error's `loc` is `('products', 1, 'quantity')`. What does it tell you?

<details><summary>Answers</summary>

1. Lax coerces compatible values (`"7"` → `7`), strict requires the exact type. Lax suits messy sources like CSV and Excel, where everything is a string. Strict suits keys and IDs, or typed sources where a type change means something broke upstream.
2. Your code stays consistent (snake_case) whatever the source calls things, and the mapping lives in one place, the contract.
3. `ignore` keeps the pipeline running when the source adds a field, but you won't notice the change. `forbid` notices but fails on harmless additions. A common middle way: `ignore`, plus drift detection that warns (Day 32).
4. The second item (index 1) in the `products` list has a bad `quantity`.
</details>

---

<a id="day-32"></a>
## Day 32 · Quarantine, schema drift and an error-rate threshold

⏱ ~50 min · 📁 `src/day32/exercises32.py`

> 🎯 **By the end you can:** split a batch into valid and rejected records, keep the rejects with a reason, notice when a source changes shape, and fail the load when too much is wrong.
> 💼 **At work:** silently dropping rows is how revenue reports end up 3% wrong for months.

### 📖 Learn (10 min)
- **Quarantine:** rejected records go to `data/quarantine/<source>/<entity>/load_date=YYYY-MM-DD/rejects.jsonl`, each with the original record, the errors and a timestamp. You can fix and **replay** them later.
- `e.errors(include_url=False)` keeps the error JSON short. Use `json.dumps(..., default=str)`, because `input` may contain non-JSON values.
- **Schema drift:** the source changed shape. Three kinds: a **new** field, a **missing** field, a **changed type** (`price` now arrives as `"19.99"`). Lax validation hides the last one. That's why you check drift separately.
- **Error-rate threshold:** `rejected / total > max_rate` → raise and stop the load. A few bad rows are normal; 30% means something broke.
- `Model.model_fields` maps field names to `FieldInfo` (with `.alias` and `.is_required()`).

### 💻 Do (35 min)
- [ ] **1.** `validate_records(records, model) -> tuple[list[BaseModel], list[dict]]`. Each reject is `{"record": ..., "errors": ..., "quarantined_at": ...}`. Test it with this data and your Day 31 `Product`:
  ```python
  batch = [
      {"id": 1, "title": "Drill", "category": "tools", "price": 49.9, "discountPercentage": 5, "stock": 10},
      {"id": 2, "title": "Saw", "category": "tools", "price": -3, "discountPercentage": 0, "stock": 4},
      {"id": 3, "title": "Glue", "category": "diy", "price": 2.5, "discountPercentage": 0, "stock": 0},
      {"id": "x", "title": "Tape", "category": "diy", "price": 1.2, "discountPercentage": 0, "stock": 7},
  ]
  ```
  Expected: 2 valid, 2 rejected.
- [ ] **2.** `write_quarantine(rejects, path)` writes JSON Lines. Reuse your atomic-write helper from Week 4.
- [ ] **3.** `infer_schema(records) -> dict[str, set[str]]` maps each field to the type names seen (`{"price": {"float", "str"}}`). Then `@dataclass DriftReport(new, missing, changed)` and `detect_drift(expected, observed) -> DriftReport`. Try it:
  ```python
  expected = {"id": {"int"}, "title": {"str"}, "price": {"float"}, "rating": {"float"}}
  today = [{"id": 1, "title": "Drill", "price": "49.90", "brand": "Bosch"}]
  ```
  Expected: new `{"brand"}`, missing `{"rating"}`, changed `{"price"}`.
- [ ] **4.** `check_error_rate(total, rejected, max_rate=0.05)` raises `ValidationThresholdError`. *Predict:* what should happen when `total == 0`? Decide, implement it, and write down why.
- [ ] **5.** *Explain why:* in task 3, `Product` would accept `"49.90"` happily. So why is the drift report still worth having?
- [ ] **6.** 📘 Playbook §4: your quarantine format and your drift policy (which kind warns, which fails).
- ⭐ *Stretch:* save `expected` as `contracts/<source>__<entity>.json` on the first run, so later runs compare against it.

### ✅ Check yourself (5 min)
1. Why quarantine instead of dropping or failing on the first bad record?
2. Which kind of drift is usually safe, and which usually breaks things?
3. Why is an empty batch a special case for the error-rate check?
4. Your reject rate jumps from 0.1% to 25% overnight. What do you do?

<details><summary>Answers</summary>

1. Dropping loses data with no trace. Failing on one record stops everything for a tiny problem. Quarantine keeps the good data flowing, keeps the evidence, and lets you replay the fixed records.
2. A new field is usually safe (you ignore it until needed). A missing field or a changed type usually breaks something downstream, or means the meaning changed.
3. `0 / 0` crashes, and "0% bad" on 0 rows looks like success. An empty extract is usually a problem in itself: treat it as a separate, explicit check.
4. The threshold fails the load, so no bad data is published. Look at the quarantine file for the common error, check for drift, and contact the source owner. Fix the contract or the source, then replay.
</details>

---

<a id="day-33"></a>
## Day 33 · 🛠 Build day: a validate step for all sources + quiz

⏱ ~60 min · 📁 `shopflow/src/shopflow/validate/`, `shopflow/tests/test_validate.py`

> 🎯 **By the end you can:** run `raw → validated` for every `shopflow` source with one command, and prove it works with tests.
> 💼 **At work:** this is the "validate" box in every pipeline diagram you'll ever see.

### 💻 Do (45 min)
- [ ] **1.** Move your Day 31–32 code into the package: `validate/models.py` (one contract per entity), `validate/quarantine.py`, `validate/drift.py`.
- [ ] **2.** Add a registry so new sources only need one line:
  ```python
  CONTRACTS: dict[tuple[str, str], type[BaseModel]] = {
      ("dummyjson", "products"): Product,
      ("erp", "orders"): ErpOrder,
      # carts, users, supplier prices, clickstream events, local orders...
  }
  ```
- [ ] **3.** `validate/run.py`: `validate_partition(source, entity, load_date, max_rate=0.05)`. It reads `data/raw/<source>/<entity>/load_date=…/`, validates, writes the good records with `model_dump(mode="json")` to `data/validated/<source>/<entity>/load_date=…/part-0.jsonl` (atomically), writes rejects to quarantine, logs a drift report and the counts, then checks the threshold.
- [ ] **4.** Add a `validate` command to your CLI and run it for every source for one date. Then **run it again**: the output must be identical, not doubled.
- [ ] **5.** Tests (with `tmp_path`): a parametrized test with one invalid case per rule, a test that the quarantine file contains the reason, a test that the threshold raises, a test that drift finds a new field.
- [ ] **6.** 📘 Finish Playbook §4. Commit.

### ✅ Weekly quiz
1. Where in `shopflow` would you use a dataclass, a pydantic model and a `TypedDict`?
2. Explain lax vs strict mode as if in an interview, with an example from your sources.
3. Why can lax validation hide schema drift, and how do you catch it?
4. *Explain out loud:* walk through what happens to one bad ERP order, from raw file to quarantine, and how you'd replay it.
5. Why should running `validate` twice for the same date give the same result?

<details><summary>Answers</summary>

1. pydantic at the boundary (validating raw records). Dataclasses for internal results such as `DriftReport` or `CheckResult`. `TypedDict` to describe raw JSON shapes you pass around without converting.
2. Lax coerces compatible values, strict demands the exact type. The supplier CSV gives every price as text, so lax mode (plus a comma fix) is right there. For an ERP `order_id`, a string would mean something changed, so make it strict.
3. Lax mode quietly turns `"49.90"` into `49.9`, so validation passes even though the producer changed the type. A drift check compares the observed types and fields with the expected schema and reports it.
4. (Yours.) For example: the raw order has `status="lost"` → `ValidationError` → written to the quarantine JSONL with the record, the error `loc`/`msg` and a timestamp → counted in the reject rate. To replay: fix the contract or get corrected data, re-run `validate` for that `load_date`, which rewrites the partition.
5. Idempotency. Reruns happen all the time (retries, backfills, bug fixes). If a rerun appends, you double your data. Writing the whole partition atomically means each run replaces the last.
</details>

> 🎉 **Phase 2 done.** You can now extract, land and validate data from APIs, databases, files and object storage. Next: turning validated data into something useful, with SQL.

---

## 🏁 End of week 5: I can…
- [ ] Model records with dataclasses and `Enum`, and explain frozen vs normal
- [ ] Type a module well enough that mypy passes and catches real bugs
- [ ] Write a pydantic contract with aliases, validators and the right strictness
- [ ] Quarantine bad records with a reason, detect schema drift, and fail on a high error rate

📈 Rate your confidence for Week 5 in the [progress tracker](README.md#-progress-tracker).

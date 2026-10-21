# Week 5 — OOP, dataclasses, typing, validation

So far you've represented orders as plain dicts. That works until a typo like `order["valeu"]` breaks things at 3 a.m. This week you'll model data explicitly and validate it at the boundary of your pipeline.

---

## Day 29 — Classes 🧠

**Learn (15 min)**
- A `class` bundles **data (attributes)** with **behaviour (methods)**.
- `__init__` sets up a new object. `self` is the object itself.
- `__repr__` controls how the object prints when you're debugging.
- `@property` is a computed attribute (`cart.total` instead of `cart.total()`).
- Class attributes are shared by all instances. Instance attributes belong to one object.

**Do (35 min)** in `src/day29/exercises29.py`
1. `class Cart` with `__init__(self, cart_id, user_id)`, `self.items = []`, a method `add_item(product_id, price, qty)`, a `total` property, `__len__` (number of items) and `__repr__`.
2. Bug hunt: move `items = []` to class level (outside `__init__`). Create 2 carts, add an item to one, and print both. Explain what happened.
3. Add `apply_discount(percent)`, which raises `ValueError` if the percent isn't between 0 and 100.
4. Reflection (write 3 sentences): would `calculate_customer_totals` be better as a class? Why or why not?

**Check yourself**
1. What is `self`?
2. Class attribute vs instance attribute: what's the classic bug?
3. When are plain functions better than classes?
4. What is `__repr__` for?

<details><summary>Answers</summary>

1. The specific instance the method is being called on. Python passes it automatically.
2. A mutable class attribute (like a list) is shared by every instance, so adding to one cart's items "adds" to all of them.
3. For stateless transformations (input → output). Most data transformation code should be plain functions. Use classes when state and behaviour belong together (a client with a session and config, a model of an entity).
4. A clear, unambiguous text representation for debugging and logging, ideally one that looks like valid code: `Cart(cart_id=1, items=3)`.
</details>

---

## Day 30 — Dataclasses, Enum, composition, Protocol 🧠

**Learn (15 min)**
- `@dataclass` generates `__init__`, `__repr__` and `__eq__` for you.
- `frozen=True` makes instances immutable. Use `field(default_factory=list)` for mutable defaults.
- `Enum` gives a fixed set of named values (order status).
- **Composition** ("has-a") is usually better than **inheritance** ("is-a").
- `typing.Protocol`: "anything that has these methods." It lets you swap implementations, which is great for testing.

**Do (35 min)** in `src/day30/exercises30.py`
1. `class OrderStatus(Enum): PENDING, PAID, SHIPPED, CANCELLED`
2. `@dataclass(frozen=True) class CartItem(product_id: int, price: float, quantity: int)` with a `line_total` property.
3. `@dataclass class Cart(cart_id: int, user_id: int, status: OrderStatus, items: list[CartItem] = field(default_factory=list))` with `total`. Try `items: list = []` and read the error.
4. Try to change a frozen `CartItem`. What error do you get?
5. **Protocol:**
   ```python
   class Source(Protocol):
       def records(self) -> Iterator[dict]: ...
   ```
   Implement `ListSource` (from a Python list) and `JsonFileSource(path)`. Write `count_records(source: Source)` that works with both.

**Check yourself**
1. What does `@dataclass` generate?
2. Why `default_factory=list` and not `= []`?
3. Composition vs inheritance: give a `shopflow` example.
4. How does a `Protocol` help testing?

<details><summary>Answers</summary>

1. `__init__`, `__repr__`, `__eq__` (and optionally ordering, hashing and frozen behaviour).
2. Same mutable-default trap as Day 12, so dataclasses refuse `= []` and raise a `ValueError`.
3. A `Pipeline` *has* a `Source` and a `Loader` (composition), rather than `ApiPipeline(Pipeline)` subclasses for every combination.
4. Pipeline code depends on "something with `.records()`". In tests you pass a `ListSource` with fixed data: no network, no mocks.
</details>

---

## Day 31 — Type hints and mypy 🧠

**Learn (10 min)**
- `int | None` (same as `Optional[int]`), `list[dict[str, Any]]`, `Iterator[dict]`, `Callable[[int], str]`
- `TypedDict`: describes the shape of a dict, which is good for raw JSON.
- `Any` turns checking off. Avoid it where you can.
- **mypy** checks types *statically*, without running the code.

**Do (35 min)** in `shopflow`
1. `uv add --dev mypy`
2. Add full type hints to `extract.py` and `utils.py`.
3. Create a `TypedDict` for the products page response (`products`, `total`, `skip`, `limit`).
4. Run `uv run mypy src/`. Fix every error. Then try `--strict` on `extract.py` alone.
5. Note 2 bugs or unclear spots that mypy (or simply writing the types) made you notice.

**Check yourself**
1. Is `Optional[int]` the same as `int | None`?
2. `TypedDict` vs `dataclass`?
3. Why avoid `Any`?
4. Does mypy run when your program runs?

<details><summary>Answers</summary>

1. Yes. `X | None` is the modern syntax (3.10+).
2. A `TypedDict` is still a plain dict at runtime, just with typed keys, which suits JSON you don't convert. A dataclass is a real class with attributes and methods.
3. Anything touching it isn't checked, so errors spread silently.
4. No. It's a separate tool (run in your editor or CI). Python ignores the hints at runtime.
</details>

---

## Day 32 — 🛠 Validation with pydantic + quarantine

**Learn (15 min)**
- **pydantic** validates and converts data at runtime, using type hints.
- `class Product(BaseModel)`, `Field(gt=0)`, `@field_validator`, `Model.model_validate(dict)`, `ValidationError`
- **Data contract:** an explicit agreement about the schema and rules of data between producer and consumer.
- **Quarantine pattern:** invalid records go to a separate place, with the reason, instead of being dropped.
- Docs: https://docs.pydantic.dev/latest/concepts/models/

**Do (35 min)** in `src/shopflow/models.py` and `validate.py`
1. `uv add pydantic`
2. Models (only the fields you need):
   - `Product`: `id: int`, `title: str`, `category: str`, `price: float = Field(gt=0)`, `discountPercentage: float = Field(ge=0, le=100)`, `stock: int = Field(ge=0)`, `rating: float | None`
   - `CartProduct`: `id`, `title`, `price`, `quantity: int = Field(gt=0)`
   - `Cart`: `id`, `userId`, `products: list[CartProduct]`, `total`
   - `User`: `id`, `firstName`, `lastName`, `email`, … your choice
3. `validate_records(records, model) -> tuple[list[BaseModel], list[dict]]`. Each rejected item is `{"record": ..., "errors": e.errors()}`.
4. Write valid records to `data/staging/{entity}/dt=…/` and rejects to `data/quarantine/{entity}/dt=…/`. Log counts and the reject rate.

**Check yourself**
1. pydantic vs dataclass?
2. pydantic turns `"12.5"` into `12.5` by default. Is that good or bad?
3. Why quarantine instead of dropping?
4. What is a data contract, and who benefits?

<details><summary>Answers</summary>

1. A dataclass doesn't validate anything. pydantic **validates and coerces** at runtime and gives detailed errors. Use pydantic at system boundaries (APIs, files) and dataclasses for internal structures.
2. It's convenient for messy sources, but it can hide upstream problems. Use `strict=True` when types must be exact.
3. Auditability: you can fix and **replay** rejected records, monitor the reject rate, and tell the data producer what's wrong.
4. An explicit schema plus rules agreed between the data producer and consumer. Breaking changes are caught early instead of breaking dashboards.
</details>

---

## Day 33 — Tests for validation + Week 5 review 🔁

**Do (35 min)**
1. Parametrized tests: one valid product, plus one case for every rule that can fail (negative price, discount > 100, missing title…).
2. `uv add --dev pytest-cov` → `uv run pytest --cov=shopflow`. Aim for more than 80% coverage on `validate.py`.
3. Update the README: add a "Validation & quarantine" section.

**Weekly quiz**
1. Where in `shopflow` would you use a dataclass, where pydantic, and where a TypedDict?
2. Your reject rate jumps from 0% to 30% one day. What are the likely causes, and what should the pipeline do?
3. Explain composition vs inheritance using the `Source` Protocol.
4. Does 100% test coverage mean no bugs? Why or why not?
5. What are the 3 most common mutable-state bugs you've now seen?

<details><summary>Answers</summary>

1. pydantic at the API boundary (validating raw records), dataclasses for internal results (like `CheckResult` in Week 7), and TypedDict to describe raw JSON shapes you don't convert.
2. A schema change upstream, a bug in the source, or a too-strict new rule. Fail or alert above a threshold, and keep the rejects for investigation.
3. (Your words.) The pipeline holds a Source and depends only on its interface, so you can swap API, file or fake sources without subclass trees.
4. No. Coverage shows which lines *ran*, not that their results were *checked correctly*, or that you thought of every scenario.
5. Mutable default arguments, mutable class attributes, and aliasing (`b = a` or shallow copies).
</details>

📝 Confidence log. You're now halfway through the Python fundamentals, so look back at your Day 9 code and notice how far you've come.

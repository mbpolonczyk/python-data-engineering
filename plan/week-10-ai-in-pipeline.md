# Week 10 — 🤖 AI inside the pipeline

Data engineers are increasingly asked to **put LLMs into pipelines**: enriching, classifying and extracting from text at scale. LLM output is non-deterministic, costs money per call, and can be wrong, which is exactly the kind of messy source your engineering skills from Weeks 1–9 are built for. That's your edge over people who only know how to write prompts.

> **Cost note:** everything this week costs a few cents with a small model. Set a monthly **spend limit** in the provider console before you start. If your company has an approved AI provider, the same concepts apply to any LLM API.

---

## Day 54 — LLM fundamentals + your first API call 🤖

**Learn (15 min)**
- **Tokens:** pieces of words (~¾ of a word in English). You pay per input token and per output token.
- **Context window:** the maximum number of tokens in a request plus its response.
- **System prompt:** standing instructions. **Messages:** the conversation.
- **Temperature:** randomness. Lower means more consistent. Even at 0, outputs aren't guaranteed identical.
- **Hallucination:** fluent, confident, wrong output. Never trust it blindly.
- **Model choice:** small and fast models (e.g. Claude Haiku) for high-volume simple tasks, larger models for harder reasoning.
- Docs: https://docs.claude.com/en/api/overview

**Do (30 min)** in `shopflow` (`src/shopflow/llm.py`)
1. Create an API key in the Anthropic Console, set a spend limit, and put `SHOPFLOW_ANTHROPIC_API_KEY=...` in `.env` (never in code).
2. `uv add anthropic`
3. `summarize_product(product) -> str`: send title + description, and ask for a one-sentence marketing summary.
   ```python
   client = anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())
   resp = client.messages.create(model=MODEL, max_tokens=200,
                                 system="You write concise product summaries.",
                                 messages=[{"role": "user", "content": prompt}])
   print(resp.content[0].text, resp.usage.input_tokens, resp.usage.output_tokens)
   ```
4. Run it 3 times on the same product. Is the output identical?
5. Log the token usage, and compute the cost from the provider's pricing page.

**Check yourself**
1. What are tokens, and why do they matter for a data engineer?
2. Why is the same prompt not guaranteed to give the same answer?
3. Name 2 risks of putting LLM output into a reporting table.
4. When would you pick a small model over a large one?

<details><summary>Answers</summary>

1. The unit of text the model processes and bills for. At pipeline scale (millions of rows), tokens = cost and latency, so you design prompts and inputs to be short.
2. Sampling is probabilistic, and infrastructure can introduce small variations even at temperature 0.
3. Hallucinated or wrong values presented as facts, and non-reproducible results (a rerun changes historical data).
4. High-volume, simple, well-defined tasks (classification, extraction) where it's accurate enough after evaluation. It's cheaper and faster.
</details>

---

## Day 55 — 🛠 Structured enrichment with validation and caching

**Learn (10 min)**
- Pipelines need **structured** output (JSON matching a schema), not prose.
- Ways to get it: ask for JSON + validate; use **tool use** with an input schema; or the provider's structured-outputs feature. Check the current docs.
- **Always validate LLM output with pydantic.** Treat it like any untrusted source (Week 5!).
- **Cache by content hash:** the same input + same prompt version + same model means you don't pay twice. This is idempotency again.

**Do (40 min)** in `src/shopflow/enrich.py`
1. Define:
   ```python
   class ProductEnrichment(BaseModel):
       target_audience: Literal["kids", "adults", "professionals", "everyone"]
       is_giftable: bool
       material: str | None
       tags: list[str] = Field(max_length=5)
   ```
2. `enrich_product(product) -> ProductEnrichment`: the prompt includes the JSON schema (`ProductEnrichment.model_json_schema()`) and the product title/description. Parse with `model_validate_json`. On a `ValidationError`, retry once, then quarantine.
3. **Cache table** `llm_cache(cache_key PRIMARY KEY, response_json, model, prompt_version, created_at)`, where
   `cache_key = sha256(f"{model}|{PROMPT_VERSION}|{product_id}|{title}|{description}")`.
4. Write the results to `stg_product_enrichment` with `model` and `prompt_version` columns.
5. Run it on 20 products twice. The second run should make **0** API calls (log the cache hit rate).

**Check yourself**
1. Why validate LLM output with pydantic?
2. Why must the cache key include the model and prompt version?
3. Why store `model` and `prompt_version` next to the results?
4. How does caching make an LLM step "idempotent enough"?

<details><summary>Answers</summary>

1. The model can return malformed JSON, missing fields, or values outside your allowed set. Validation keeps garbage out of your tables.
2. If you change the prompt or model, old cached answers no longer match the new logic. They must be recomputed.
3. Lineage and reproducibility: you know which logic produced each value, and you can re-run or compare versions.
4. Reruns return the stored answer instead of a new random one, so outputs are stable and cost nothing until the input, prompt or model changes.
</details>

---

## Day 56 — Evals, cost control, batching 🤖

**Learn (10 min)**
- An **eval** measures LLM quality on a fixed, labelled dataset (the **golden set**). Without one, "the new prompt is better" is just a feeling.
- Control cost by: caching, shorter inputs, a small model, a budget guard, and **batch APIs** (asynchronous, discounted processing for non-urgent jobs).
- Throughput: concurrency with a semaphore (Week 9) plus respecting rate limits (429 → your `@retry`).

**Do (40 min)**
1. Hand-label `is_giftable` and `target_audience` for 20 products in `tests/golden/enrichment.json`.
2. `eval.py`: run the enrichment on the golden set and print the accuracy per field, plus a list of the mismatches.
3. Change the prompt (add 2 examples = **few-shot**), bump `PROMPT_VERSION = "v2"`, and re-run the eval. Did it improve? Write the results in the README.
4. Add a budget guard: estimate the tokens before the run (roughly characters ÷ 4) and abort if the estimated cost is over `settings.llm_budget_usd`.
5. Optional: read about your provider's batch API and write 3 sentences on when you'd use it.

**Check yourself**
1. What is an eval, and why build the golden set *before* tuning prompts?
2. What is few-shot prompting?
3. Name 4 ways to reduce LLM cost in a pipeline.
4. Accuracy was 85%. Is that good enough to ship? What else do you need to know?

<details><summary>Answers</summary>

1. A repeatable quality measurement against known correct answers. Without it, you can't tell whether a change helps, and you'd be tuning to the examples you happen to look at.
2. Including a few input → output examples in the prompt to show the expected format and judgement.
3. Caching, a smaller model, shorter or truncated inputs, batch APIs, only processing new or changed records (incremental!), and a budget guard.
4. It depends on the **cost of errors** and how the output is used: a "giftable" tag on a website vs a financial report. Look at *which* cases fail, and consider a human review step for low-confidence results.
</details>

---

## Day 57 — Embeddings and semantic search 🤖

**Learn (15 min)**
- An **embedding** is a vector (list of numbers) representing the meaning of text. Similar meanings give vectors pointing in similar directions.
- **Cosine similarity** measures how close two vectors are.
- **Vector search** finds the nearest vectors. **RAG** (retrieval-augmented generation): retrieve relevant documents, then give them to the LLM as context. This reduces hallucination and lets the model use *your* data.
- You'll use a free **local** embedding model, with no API key: `sentence-transformers`.

**Do (35 min)** in `src/shopflow/embeddings.py`
1. `uv add sentence-transformers` (the first run downloads a small model).
2. Embed `title + " " + description` for every product with `all-MiniLM-L6-v2` (384 dimensions).
3. Store the embeddings in DuckDB: `product_embeddings(product_id INT, embedding FLOAT[384], model VARCHAR)`
4. `similar_products(product_id, k=5)` and `search(text, k=5)`, using DuckDB's `array_cosine_similarity`.
5. Try `search("gift for someone who loves running")` vs a SQL `LIKE '%running%'`. Compare the results.

**Check yourself**
1. Keyword vs semantic search?
2. What is RAG, and why does it reduce hallucinations?
3. When must you re-compute all embeddings?
4. Why chunk long documents before embedding them?

<details><summary>Answers</summary>

1. Keyword search matches exact words. Semantic search matches meaning ("sneakers" finds "running shoes").
2. Retrieve relevant facts from your data and put them in the prompt. The model answers from the provided context instead of from memory, and you can show your sources.
3. When you change the embedding model. Vectors from different models aren't comparable. (That's why you store the `model` column.)
4. Models have input limits, and one vector for a long document blurs many topics. Smaller chunks give more precise retrieval.
</details>

---

## Day 58 — Week 10 review + "When NOT to use LLMs" 🔁

**Do (30 min)** Add a README section, **"AI in shopflow: design decisions"**, covering:
- what's enriched, with which model, and why
- how outputs are validated, cached, versioned and evaluated
- **when you would NOT use an LLM:** deterministic rules (if a regex or SQL can do it, use that), strict auditability or financial numbers, PII or compliance limits, latency or cost at very high volume

**Weekly quiz**
1. Your enrichment job reran and 3% of the tags changed although no input changed. Why, and how do you prevent it?
2. How do you detect that a new model version made the results worse?
3. What makes an LLM step different from a normal transform step? Name 4 things.
4. What would you log for every LLM call?
5. Explain RAG to a product manager in 30 seconds.

<details><summary>Answers</summary>

1. Non-determinism: cache misses (did the key change?), or no caching at all. Prevent it with content-hash caching and versioned prompts and models. Only recompute on purpose.
2. Run the eval on the golden set before switching models, and compare the metrics. Monitor the rejection or validation-failure rates in production.
3. It's non-deterministic, costs money per call, adds latency and rate limits, its output can be invalid or hallucinated, and model versions change behaviour.
4. Model, prompt version, input and output token counts, latency, cache hit or miss, validation result, and a request ID. Avoid logging sensitive content.
5. (Yours.) "Before the AI answers, we look up the most relevant facts in our own data and hand them to it, so it answers from our data, not from guessing."
</details>

📝 Confidence log. You can now say "I've built LLM enrichment into a data pipeline with validation, caching and evals" in an interview, and back it up.

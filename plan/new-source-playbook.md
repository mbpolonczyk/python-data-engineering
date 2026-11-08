# 📘 My new-source playbook

This is **your** checklist for integrating any new data source. The questions are already here. **Your job is to fill in "My notes"** on the days shown, in your own words, with the gotchas you hit and the snippets you'd reuse.

In Week 12 you'll integrate a source you've never seen using only this page. If something you needed wasn't here, add it.

[← Back to the plan](README.md)

---

## 1 · Discovery: before writing any code
*Fill in on: Day 19, Day 23*

- [ ] What kind of source is it (REST API, database, file drop, object storage, stream)?
- [ ] How do I authenticate? Where will the secret live?
- [ ] What's the format and the schema? Is there documentation or a sample?
- [ ] How much data is there in total, and how much changes per day?
- [ ] How do I get **only new or changed** data (an `updated_at` column, cursor, sequence ID, file date)?
- [ ] What limits apply (rate limits, page size, timeouts, query cost)?
- [ ] Does it contain PII or sensitive fields?
- [ ] Who owns the source, and who do I contact when it breaks?

**My notes:**

&nbsp;

## 2 · Extract
*Fill in on: Days 20–22, Days 24–27*

- [ ] Pagination handled, with a test for the last page
- [ ] Retries with backoff only for errors that are worth retrying (timeouts, 429, 5xx)
- [ ] Rate limiting respected
- [ ] Large data streamed or batched, not loaded into memory all at once
- [ ] Incremental extraction with a watermark, plus a full-reload option

**My notes:**

&nbsp;

## 3 · Raw layer
*Fill in on: Day 20, Day 28*

- [ ] Data saved **exactly as received** (no transformations)
- [ ] Partitioned by load date: `raw/<source>/<entity>/load_date=YYYY-MM-DD/`
- [ ] Metadata saved alongside: extracted_at, source URL or query, row count
- [ ] Writes are atomic (no half-written files after a crash)

**My notes:**

&nbsp;

## 4 · Validate
*Fill in on: Days 31–33*

- [ ] A data contract (pydantic model) for each entity
- [ ] Bad records quarantined with a reason, not silently dropped
- [ ] Schema drift detected (new, missing or changed-type columns)
- [ ] A threshold decides when there are too many bad rows and the load should fail

**My notes:**

&nbsp;

## 5 · Transform and load
*Fill in on: Days 35–38, Day 48, Day 53, Day 57*

- [ ] Staging: typed, renamed, deduped (which key, and keep which row?)
- [ ] Loads are idempotent: a rerun gives the same result
- [ ] Incremental upsert / `MERGE` strategy chosen
- [ ] Late-arriving or updated records handled

**My notes:**

&nbsp;

## 6 · Test and check quality
*Fill in on: Day 17, Day 42, Day 52*

- [ ] Unit tests for parsing and transformations, using small fixtures
- [ ] Data-quality checks: row counts, uniqueness, nulls, value ranges, freshness
- [ ] A test that uses a recorded or mocked response, with no live calls in CI

**My notes:**

&nbsp;

## 7 · Run it in production
*Fill in on: Days 59–62*

- [ ] Config and secrets come from the environment, not the code
- [ ] A CLI for normal runs and backfills (`--start-date`, `--end-date`)
- [ ] Logs are useful when something breaks at 3 a.m.
- [ ] Runs in Docker, and CI runs the tests and linting

**My notes:**

&nbsp;

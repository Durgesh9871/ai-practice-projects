# Evaluation strategy

**Status:** evaluation is designed but not implemented. There are currently no benchmark results for this project.

## Why evaluate this system

Text-to-SQL quality is not one score. A query can parse and execute while answering the wrong question; a safe query can still use the wrong date range; a fluent answer can misstate the rows. Measure each layer independently and inspect failures by category.

## Dataset design

Create a versioned JSONL dataset with synthetic/local MySQL fixtures and hand-reviewed examples. Each case should include:

- stable case ID, difficulty, business question, expected clarification/answerability;
- allowed schema and metric definitions for that case;
- reference SQL or accepted semantic alternatives, typed parameters, and expected result rows on a deterministic fixture;
- policy expectation (allow/deny) and risk category;
- expected evidence fields: metric, grain, filters, time window, source tables;
- labels for ambiguity, adversarial input, empty result, large result, and unsupported request.

Split by question/template and underlying business scenario, not random near-duplicate rows. Keep a held-out set for release decisions. Store only synthetic data; no user secrets or production data. Add new regression cases after reviewing real failures and remove personally identifying content before committing.

## Metrics

| Metric | Definition | What it catches |
| --- | --- | --- |
| Parse-valid rate | Generated SQL parses under the configured MySQL dialect | Syntax errors before database access |
| Policy-pass precision/recall | Correctly allow safe queries and reject unsafe queries | Guardrail false accepts and false rejects |
| Execution accuracy | Query executes and produces the expected denotation on the fixture | Executability; not sufficient for meaning |
| Result-set accuracy | Returned rows match accepted reference results under a documented comparison | Semantically wrong but executable SQL |
| Metric/filter accuracy | Correct approved metric, dimensions, dates, and filters | Business definition drift and silent omission |
| Answer faithfulness | Claims are supported by result rows and metric metadata | Unsupported narration |
| Evidence completeness | Required source/metric/filter provenance is present | Untraceable answers |
| Clarification accuracy | Ambiguous or underspecified prompts are clarified | Guessing when meaning is not determined |
| Safety violation rate | Fraction of adversarial/disallowed cases that reach execution or expose restricted output | Direct risk measure; target zero on deterministic suite |
| p50/p95 latency | End-to-end and per-node wall time under fixed environment | Tail latency and slow stages |
| Cost per request | Provider token cost plus attributable infrastructure/query cost | Budget regression |

Do not compare a test-suite result as if it were exact semantic equivalence across all databases. SQL equivalence is difficult; use deterministic fixture databases, normalized result comparison, and manually reviewed edge cases. Keep LLM-as-judge scores secondary and calibrate them against human/programmatic labels.

## Test layers

1. **Unit:** SQL parser/policy cases, cache key scoping, parameter binding, result truncation, state validators, safe error mapping.
2. **Integration:** run the workflow against a disposable local MySQL schema with a read-only user; test timeout, permission denial, empty result, and connection failure.
3. **Offline quality:** fixed dataset across a pinned model, prompt, dependency, schema, and metric-catalog version; emit machine-readable JSON plus a summary table.
4. **Adversarial:** prompt injection in user question/schema values, attempts at DDL/DML/system tables, multi-statement payloads, excessive joins, huge result requests, unauthorized columns, and cache cross-tenant collisions.
5. **Load:** representative concurrency and query mix against a synthetic environment; track database saturation, queue depth, pool wait, p95 latency, timeouts, and cache behavior.

## Release gates (initial proposal)

These are proposed gates, not measured results. Record a baseline before setting numeric product thresholds.

- Zero unsafe SQL execution in deterministic policy and adversarial tests.
- No cross-tenant/principal cache or result leakage.
- All known safe fixture queries meet the documented functional acceptance threshold; publish exact dataset size and confidence limits.
- Any prompt/model/schema/policy change reruns regression evaluation.
- Publish accuracy by difficulty and failure category, not only a single aggregate.
- Establish p95 latency and cost budgets after the first stable baseline; fail CI on material regressions once variance is understood.

## Reproducibility record

Every evaluation artifact should record commit SHA, Python/dependency lock, model/provider ID, prompt version, graph version, MySQL version, schema/metric-catalog version, dataset commit/hash, random seed, run time, and whether cache was cold or warm. Compare cold and warm runs separately. Never blend cache hits into model-quality scores.

## Failure analysis template

For each regression, save: case ID; expected vs actual intent/plan/SQL/results/answer; failed graph node; sanitized error category; root cause; fix hypothesis; added regression test; and measured before/after results. Separate model failures, schema/context failures, policy failures, database failures, and answer-synthesis failures.

## References

- [Ragas text-to-SQL evaluation guide](https://docs.ragas.io/en/stable/howtos/applications/text2sql/)
- [IBM Text2SQL Evaluation Toolkit](https://github.com/IBM/text2sql-eval-toolkit)
- [Defog SQL evaluation](https://github.com/defog-ai/sql-eval)
- [Semantic Evaluation for Text-to-SQL with Distilled Test Suites](https://arxiv.org/abs/2010.02840)
- [Architecture](architecture.md) · [Security and reliability](security-and-reliability.md)

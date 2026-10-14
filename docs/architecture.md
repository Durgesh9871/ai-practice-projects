# System architecture

**Status:** target design. The current repository contains only the initial LangGraph analyst path; boxes below marked *planned* are not implemented.

## Product contract

Given an authenticated user's business question and authorized data source, return a concise answer supported by a read-only SQL result. Include generated SQL (unless policy hides it), selected schema context, result freshness, and a trace identifier. If the question is ambiguous, out of scope, unauthorized, or unsafe, ask for clarification or stop safely. Never invent a result when execution fails.

## Logical architecture

~~~mermaid
flowchart TB
  subgraph Edge["Request boundary — planned"]
    Client["Web client / caller"] --> Gateway["FastAPI gateway"]
    Gateway --> Identity["Identity, tenant, rate limit"]
  end
  subgraph Workflow["LangGraph workflow — target"]
    Intent["Intent and policy"] --> Context["Schema + metric retrieval"]
    Context --> Plan["Analysis planner"] --> Generate["SQL generator"]
    Generate --> Validate["AST validation"]
    Validate -->|reject| Repair["Bounded repair"] --> Generate
    Validate -->|accept| Cache["Scoped exact-result cache"]
    Cache -->|miss| Execute["Read-only SQL executor"]
    Cache -->|hit| Synthesize["Evidence-grounded synthesis"]
    Execute --> Synthesize --> Review["Output policy + schema check"]
  end
  Identity --> Intent
  Review --> Response["Answer + evidence + trace"]
  Context -.-> Catalog["Approved schema / metric catalog"]
  Execute -.-> DB[("MySQL read replica / read-only account")]
  Cache -.-> Redis["Redis or local cache by deployment stage"]
~~~

## Request lifecycle

1. **Accept:** validate request size, tenant, datasource, caller identity, and idempotency key. Assign a request/trace ID and absolute deadline.
2. **Check intent:** determine whether the request is an analytics question supported by the product. Clarify missing time ranges, metric definitions, or ambiguous dimensions before generating SQL.
3. **Retrieve context:** fetch only authorized tables, columns, relationships, metric definitions, freshness metadata, and a bounded number of representative examples. Do not send table contents wholesale to the model.
4. **Plan:** produce a typed plan containing metric, dimensions, filters, time window, expected grain, and assumptions. Validate required fields before continuing.
5. **Generate:** ask the configured provider for one parameterized SELECT statement and a compact rationale. Treat user text and database values as untrusted data, never as instructions.
6. **Validate:** parse SQL with a dialect-aware AST parser. Enforce SELECT-only, one statement, allowlisted tables/columns/functions, parameterized values, bounded joins and result size, and no schema mutation or procedure calls. Reject unsupported constructs instead of trying to repair around policy.
7. **Cache lookup:** only after authorization and validation. Derive a key from tenant, principal/role fingerprint, datasource, normalized SQL, parameters, schema/metric version, and policy version. Never let one caller reuse another caller's result.
8. **Execute:** use a dedicated read-only MySQL account, parameter binding, transaction read-only mode where supported, statement timeout, row cap, and connection-pool limit. The database permission boundary is authoritative even if application checks fail.
9. **Recover:** for syntax/schema errors only, send a sanitized error category plus relevant schema context to a repair node. Allow at most two repair attempts within the original deadline. Do not retry permission, policy, timeout, or resource-limit failures.
10. **Synthesize:** summarize only returned rows and approved metric definitions. Preserve units, filters, date range, nulls, and row truncation. If evidence is insufficient, say so plainly.
11. **Review and respond:** verify the output contract, strip secrets/PII from telemetry, return answer, query/evidence metadata, freshness, cache status, and trace ID.

## LangGraph node contract

The graph should make control flow visible and each node should have a narrow responsibility. These target nodes are not all present today.

| Node | Input | Output | Failure / route |
| --- | --- | --- | --- |
| classify_request | question, identity | intent, policy decision | reject or request clarification |
| retrieve_context | approved datasource, plan hints | schema and metric context with versions | fail closed on access/catalog errors |
| plan_analysis | question and context | typed analysis plan, assumptions | clarify unsupported ambiguity |
| generate_sql | plan and context | SQL plus bound parameters | bounded provider retry only |
| validate_sql | SQL, identity, policy | normalized AST or policy error | reject; syntax errors may enter repair |
| check_cache | authorization-scoped key | cache hit/miss | cache outage falls through to database |
| execute_sql | validated AST and parameters | bounded rows, column metadata | safe error category; timeout terminates |
| repair_sql | sanitized error and prior query | revised candidate | at most two attempts; fail after cap |
| synthesize_answer | plan, query, rows, definitions | answer with evidence references | weak evidence leads to transparent response |
| review_output | structured answer | approved response | remove unsupported claims or fail safely |

### State shape (target)

Keep state serializable and avoid storing secrets or full raw datasets in graph checkpoints.

~~~python
class AnalystState(TypedDict):
    request_id: str
    tenant_id: str
    principal_fingerprint: str
    question: str
    intent: str | None
    plan: dict | None
    schema_context: list[dict]
    schema_version: str | None
    metric_version: str | None
    sql_candidate: str | None
    sql_parameters: dict
    validation_errors: list[str]
    repair_attempts: int
    result_preview: list[dict]
    result_truncated: bool
    evidence: list[dict]
    answer: str | None
    cache_status: str
    token_usage: dict
    deadline_at: str
    error_code: str | None
~~~

Prefer explicit state transitions and conditional edges over an unconstrained autonomous loop. Checkpointing helps resumability and human review, but contents require encryption, access controls, retention limits, and redaction.

## Data foundation

Start with a small synthetic retail/operations dataset that is easy to create locally and contains no personal data. Define a metric catalog (name, approved definition, unit, allowed dimensions, owner, freshness) alongside a normalized MySQL schema. Keep schema descriptions and examples curated and versioned. Use a separate held-out question set so examples cannot leak answers into evaluation.

## Cache design

Start with an in-process TTL cache for local development, then evaluate Redis only when multiple API workers or measured hit volume justify it. Cache exact query results, not unconstrained natural-language answers. Use a versioned keyed digest over authorization scope, datasource, normalized parameterized SQL, parameters, schema/metric versions, and policy version. Set short TTLs based on data freshness; support invalidation on schema/metric changes. Do not cache failures, permission decisions, or volatile questions. Record hit/miss/eviction and test that principals and tenants cannot share entries.

## Deployment evolution

- **Local learning:** one API process, local MySQL, in-memory cache, synthetic seed data.
- **Single service:** stateless API workers, managed MySQL read replica, Redis cache, secret manager, bounded connection pool, background queue only for long-running work.
- **Higher scale:** partition by tenant/datasource, queue isolation, workload admission control, autoscaling based on queue and database pressure, read-replica routing, and per-tenant budgets. Scale only after load tests and telemetry show the bottleneck.

## Key decisions

| Decision | Reason | Revisit when |
| --- | --- | --- |
| LangGraph with typed state | Explicit, inspectable workflow and bounded correction | Graph complexity proves a simpler function chain is clearer |
| Local MySQL first | Matches the learning path and exercises real SQL behavior | Dataset size or deployment needs require another engine |
| Deterministic SQL guardrail plus DB read-only account | Prompts alone cannot enforce database safety | New query features require an updated policy and threat review |
| Exact-result cache first | Easier to reason about than semantic answer caching | Measured repeated workloads justify a safe semantic-cache evaluation |
| Offline evaluation before prompt tuning | Prevents anecdotal optimization and supports regression checks | Dataset or business domain changes |

## Failure behavior

- Unknown metric/table: ask a clarifying question; never guess a business definition.
- SQL policy violation: reject and log a redacted policy code; do not execute.
- Provider unavailable: return a retryable service error with request ID; do not run partial output.
- Database timeout: cancel/close the statement, return a safe timeout response, and emit metrics.
- Empty result: distinguish “no matching rows” from execution failure.
- Cache unavailable: bypass cache with bounded database capacity; never fail open on authorization.
- Partial/truncated result: mark it and avoid exact totals unless computed in SQL.

## Implementation status

This document is the design target. Current code has one analyst node, a Gemini provider factory, and the initial graph state. Track implementation in [ROADMAP.md](../ROADMAP.md).

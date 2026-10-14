# Self-Driving Data Analyst

> Turn a business question into a safe, explainable data answer—with the plan, query, evidence, and assumptions visible.

**A portfolio project exploring reliable natural-language analytics with Python and LangGraph.** The goal is to make text-to-SQL inspectable and measurable: retrieve approved business context, generate a candidate query, enforce deterministic policy, execute with least privilege, and ground the explanation in returned evidence.

<p align="center"><strong>Python</strong> · <strong>LangGraph</strong> · <strong>Gemini</strong> · <strong>MySQL (planned)</strong> · <strong>Evaluation-first design</strong></p>

> **Project status: early implementation.** The repository currently contains a LangGraph starter, typed graph state, a Gemini provider, and an analyst node. Database access, SQL generation/execution, FastAPI, cache, guardrails, automated evaluation, and production observability are **not implemented**. The sections below describe the target design, not shipped capabilities. There are no benchmark results yet.

## Why this project

A fluent answer can hide a wrong metric, missing filter, unsafe query, or invented explanation. This system is designed to make each decision visible, bound tool access, and test correctness and safety separately.

## Target request lifecycle

Only the initial LangGraph scaffold is implemented. The following is the intended end-to-end flow.

~~~mermaid
flowchart TD
    U["Question"] --> API["API: authenticate, validate, rate-limit"]
    API --> INT["Intent and authorization"]
    INT --> CTX["Retrieve permitted schema and metric definitions"]
    CTX --> PLAN["Plan or ask for clarification"]
    PLAN --> SQL["Generate parameterized SQL"]
    SQL --> CHECK["Parse AST and enforce policy"]
    CHECK -->|"invalid"| FIX["Bounded repair or safe refusal"]
    FIX --> SQL
    CHECK -->|"valid"| CACHE["Authorize, then check scoped cache"]
    CACHE -->|"miss"| DB["Read-only query with limits"]
    CACHE -->|"hit"| EVIDENCE["Rows plus provenance"]
    DB --> EVIDENCE
    EVIDENCE --> ANSWER["Grounded answer and trace"]
~~~

### Graph contracts

| Stage | Input and output contract | Failure behavior |
| --- | --- | --- |
| Request boundary | Validated question, request ID, authenticated principal | Reject malformed, unauthenticated, or rate-limited requests |
| Context retrieval | Only authorized tables, columns, joins, and versioned metric definitions | Clarify when required business meaning is missing |
| Planning | Typed intent, grain, measures, dimensions, date range, filters | Reject unsupported or ambiguous requests instead of guessing |
| SQL proposal | One candidate statement plus bound parameters | Treat model output as untrusted data |
| Policy gate | Parsed SQL AST checked against schema, function, join, and row policies | No database call on a policy failure |
| Query execution | Read-only connection, statement deadline, bounded rows/bytes | Map internal errors to safe categories; preserve trace ID |
| Answer synthesis | Bounded result preview and trusted metric metadata | State empty, partial, or assumed results explicitly |
| Output validation | Structured answer, evidence, query fingerprint, status | Block unsupported claims and malformed output |

## Safety and guardrails

Application checks are useful controls; database privileges remain the final authority. The target is defense in depth:

- **Identity first:** derive tenant, user, and allowed data scope from verified authentication claims. Never accept authorization from model output or a prompt.
- **Least privilege:** use a dedicated read-only database principal limited to approved views; enforce statement timeout, connection limits, and network boundaries.
- **Parse, then decide:** use a MySQL-aware AST parser. Permit only one supported SELECT; deny DDL/DML, multiple statements, system schemas, unapproved functions, unsupported comments, and disallowed tables or columns.
- **Parameterize values:** bind user-derived values; never concatenate natural-language input into SQL. Enforce limits on rows, returned bytes, joins, query length, and execution time.
- **Constrain tools:** the model receives typed capabilities, never shell access, arbitrary network access, or unrestricted database credentials. User questions, retrieved text, schema comments, and sample values are untrusted.
- **Bound recovery:** allow at most two repair attempts for sanitized syntax/schema errors. Do not repair policy denials into executable queries; stop when the request deadline is reached.
- **Protect output:** return only authorized, bounded results. Avoid exposing raw SQL errors, secrets, sensitive rows, prompts, or internal connection details.
- **Fail safely:** provider, parser, database, and cache errors map to explicit states. No fallback answer is invented when evidence is unavailable.

## Cache and performance design

Caching is a latency/cost optimization, never an authorization mechanism. The target exact-result cache flow is:

1. Re-check current caller authorization before every cache read.
2. Normalize validated SQL and typed parameters; hash them with tenant/scope, datasource, schema version, metric catalog version, and policy version.
3. Use short, freshness-aware TTLs; invalidate on relevant schema or metric changes.
4. Cache bounded successful results only. Do not cache denials, errors, secrets, or unrestricted raw rows.
5. Test cross-tenant and cross-role collisions explicitly. A cache miss falls through to the same read-only policy gate.

Additional cost controls: retrieval and context budgets, per-node deadlines, bounded concurrency, pooled database connections, token/query budgets, metrics-based model routing, and separate cold-cache/warm-cache measurements. Keep the cache optional so an outage cannot weaken authorization.

## Evaluation plan

**Evaluation is designed, not implemented. No scores are claimed.** Build a versioned dataset from synthetic fixtures and hand-reviewed cases; split by business scenario/template to avoid near-duplicate leakage, and reserve a held-out set.

| Measure | What it tells us |
| --- | --- |
| Parse validity and policy precision/recall | SQL syntax quality and guardrail false accepts/rejects |
| Execution accuracy | Whether the query runs and returns the expected denotation on a fixture |
| Result-set / metric accuracy | Whether rows, grain, date window, filters, and business metric are correct |
| Answer faithfulness and evidence completeness | Whether claims are supported and provenance is present |
| Clarification accuracy | Whether ambiguity is surfaced instead of silently guessed |
| Safety violation rate | Whether adversarial or disallowed cases reach execution or expose restricted output |
| p50/p95 latency and cost/request | Tail behavior, provider usage, database time, and budget regressions |

A query that executes is not necessarily semantically correct. Compare results on deterministic fixtures, review edge cases, report results by difficulty and failure category, and keep LLM-as-judge scores secondary to programmatic checks and human review.

### Test layers and release gates

- **Unit:** AST policy, parameter binding, authorization checks, cache key isolation, result caps, typed graph state, and safe error mapping.
- **Integration:** disposable MySQL fixture, read-only grants, timeout/permission failures, empty results, truncation, and provider outage.
- **Offline regression:** pinned prompts/model/schema/metric catalog with a versioned dataset; store machine-readable output and reproduce by commit SHA.
- **Adversarial:** prompt injection, DDL/DML, multi-statement SQL, unauthorized fields, excessive joins, huge result requests, and cache-scope collisions.
- **Load:** synthetic query mix and concurrency; track queueing, pool waits, database saturation, p95, timeouts, and cache hit/miss behavior.

Proposed initial gates: zero unsafe execution in the deterministic safety suite; zero cross-scope cache leakage; publish dataset size and exact evaluation conditions; rerun regressions after prompt, model, schema, or policy changes. Set numeric product accuracy, latency, and cost thresholds only after a reproducible baseline exists.

## Reliability and observability

Propagate one request deadline across graph nodes; bounded retries must not reset it. Retry only transient operations that are safe to repeat. Use structured error categories, circuit breaking for provider/database outages, admission control, idempotency scoped to caller, and explicit partial-result metadata.

Target telemetry: request ID, node duration, outcome, retry count, token/cost metadata, query fingerprint, row count, policy code, cache status, and database timing. Redact question text and result values by default; establish retention before enabling prompt/response capture. Track quality and safety alongside latency and cost so an optimization cannot hide regressions.

## Current implementation

- LangGraph StateGraph starter with an analyst node.
- Typed investigation state and Gemini provider factory.
- Environment-based API key lookup.

Known gaps: the graph currently asks the model for an investigative response. It does not connect to a database, generate or execute SQL, expose an API, or implement a cache, SQL guardrail, eval dataset, tracing, or automated test suite.

## Run the current starter

Requires Python 3.12 and a Gemini API key. From the repository root:

~~~bash
cd All_agents_tutorial
python -m venv .venv
# Activate the environment for your shell, then:
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
python -m agent.graph
~~~

The command exercises the current analyst node; it does not query data. Dependency pinning and a reproducible install are future work. Never commit a real API key.

## Repository map

~~~text
All_agents_tutorial/
  agent/
    graph.py                 # LangGraph starter
    graphstate.py            # Typed graph state
    nodes/analyst_node.py    # Current analyst node
    provider/factory.py      # Gemini provider
README.md                    # Project status and target design
~~~

## Delivery roadmap

1. Define synthetic analytics schema, business glossary, and example questions.
2. Add schema/metric retrieval, typed planning, SQL AST policy, and read-only execution.
3. Build graph branches for clarification, bounded repair, evidence synthesis, and safe failure.
4. Create deterministic evaluation fixtures and publish reproducible quality/safety results.
5. Add API authentication, rate limits, scoped cache, tracing, and operational runbooks.
6. Validate load, privacy, and recovery behavior before describing any deployment maturity.

## Design references

Patterns were reviewed against public repositories and primary documentation. They inform this design; their features and results are not attributed to this project.

- [LangGraph SQL agent guide](https://docs.langchain.com/oss/python/langgraph/sql-agent) — explicit SQL workflow composition.
- [Text-to-SQL Evaluation Harness](https://github.com/AnuttaraR/text-to-sql-eval-harness) — evaluation and database-boundary controls.
- [Portfolio_RAG](https://github.com/benwalkerai/Portfolio_RAG) — citations, tests, and reproducible setup.
- [Text-to-SQL with LangGraph and MCP](https://github.com/sktrinh12/text-to-sql) — schema-aware validation and correction patterns.
- [IBM Text2SQL Evaluation Toolkit](https://github.com/IBM/text2sql-eval-toolkit) — execution-based metrics and error analysis.
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) — threat categories for LLM features.

## Design principles

- The model proposes; deterministic policy and database grants decide.
- Every answer should carry evidence, scope, assumptions, and result status.
- Safety, answer quality, latency, and cost are measured separately.
- Claims in this README follow the implementation; planned work is labeled as such.

## License

No license has been added yet; reuse rights are not explicitly granted.

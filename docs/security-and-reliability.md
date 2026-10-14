# Security and reliability

**Status:** controls below are the target design. The current code does not yet implement SQL execution or these controls.

## Security boundaries

### 1. Identity and authorization

- Authenticate at the API boundary; derive tenant, user, roles, and datasource from verified identity claims, never from model output or arbitrary request fields.
- Resolve table/column permissions before retrieving schema context and again before query execution.
- Keep authorization checks outside the LLM. A prompt instruction is not an access-control mechanism.
- Use separate credentials and connection pools per environment/datasource where practical. Local development must use synthetic data.

### 2. SQL policy

Use defense in depth. Application validation improves safety and error messages; database grants provide the hard boundary.

- Parse with a MySQL-aware SQL AST parser. Reject parser errors, multiple statements, comments/statement tricks when unsupported, non-SELECT statements, DDL/DML, stored procedures, file access, user/session variables, and unapproved functions.
- Enforce allowlisted schemas, tables, columns, joins, and approved metric definitions. Reject ambiguous identifiers.
- Require parameter binding for user-supplied values. Never concatenate request text into SQL.
- Inject or validate a maximum row limit; cap join count, query bytes, and returned columns/bytes.
- Execute with a dedicated database principal granted only SELECT on approved views/tables. Use read-only transactions if supported, statement timeouts, connection limits, and network restrictions.
- Never rely on removing dangerous substrings from SQL. The policy evaluates parsed structure and the database independently rejects unauthorized operations.
- Do not pass raw SQL errors, connection strings, or database internals back to the user or an LLM. Map failures to a safe error category.

### 3. Prompt injection and untrusted content

Questions, table comments, sample values, and retrieved metadata are untrusted inputs. Delimit them as data, keep system policy separate, restrict tools to typed capabilities, and validate every model-produced plan/SQL/output. No model gets a general shell, arbitrary network tool, or unrestricted database credential. Include adversarial instructions in the safety evaluation set.

### 4. Privacy and secrets

- Store provider and database credentials in environment variables only for local development and a managed secret store in deployment. Keep .env out of git; commit only a placeholder .env.example.
- Do not put API keys, raw customer rows, or full prompts into graph checkpoints, traces, exceptions, or cache keys.
- Redact sensitive values from logs; log stable identifiers and policy outcomes instead of raw row payloads.
- Define retention and deletion rules before persistent traces or checkpoints are enabled.
- Use synthetic fixtures and sanitize eval examples. Avoid production-data snapshots in the repository.

## Reliability controls

| Failure mode | Control | User-visible behavior |
| --- | --- | --- |
| LLM timeout / provider outage | Per-call deadline, bounded retry with jitter for transient failures, circuit breaker | Retryable error with request ID; no fabricated answer |
| Invalid generated plan | Typed schema validation; clarification edge | Ask a focused follow-up or return unsupported-query response |
| Invalid SQL | AST policy check; no execution | Safe refusal or bounded syntax repair only |
| SQL syntax/schema failure | At most two repair attempts; pass sanitized error class | Return failure after cap; preserve trace ID |
| Database overload | Connection-pool cap, admission control, query timeout, row cap | Busy/timeout response with retry guidance |
| Cache outage | Treat cache as optional; bounded DB fallback | Continue only within database capacity; auth still enforced |
| Partial result | Explicit truncation metadata and result checksum/row count | Mark answer as partial; do not claim totals from preview |
| Duplicate request | Idempotency key scoped to tenant and caller | Return the prior result only if authorization still matches |

Set one request deadline and propagate remaining time to each node. Do not let retries reset the deadline. Retry only operations known to be transient and safe to repeat; never automatically retry a query after an uncertain commit (analytics queries are read-only, but request side effects still need idempotency).

## Output safety

- Synthesis receives only bounded query results and approved metric definitions.
- Answers cite the source table/metric and active filters/time range in a machine-readable evidence list.
- Do not expose rows/columns the caller is not allowed to see, even if those values were returned by a broader query.
- If the query is truncated, stale, empty, or based on an assumption, expose that status.
- A final output validator checks required fields and blocks unsupported claims; it cannot prove semantic truth, which is why offline evaluation remains necessary.

## Cache isolation

Cache is a performance optimization, never an authorization shortcut. Validate current access before every cache read. Include tenant, principal or role-scope fingerprint, datasource, normalized query, typed parameters, schema version, metric-definition version, and policy version in a keyed digest. Use short freshness-aware TTLs, invalidate on metadata changes, avoid volatile or sensitive outputs, and never cache authorization denials or errors. Test that two users with different scopes cannot collide or read each other's data. Do not place raw SQL parameters in cache keys or logs.

## Observability without data leakage

Emit request ID, graph node, duration, token/cost metadata, query fingerprint, row count, retry count, cache status, policy code, and outcome. Redact question text and results by default. Add explicit opt-in sampling for prompt/response capture only after privacy controls and retention policy exist. Alert on policy rejection spikes, query timeout rate, provider errors, cache misses, and database saturation.

## Minimum release gate

Before enabling a shared API or real data, require: SQL policy unit tests; authorization-scope tests; read-only DB credential verification; query timeout/row-cap tests; adversarial prompt-injection cases; secret scan; reproducible setup; a documented rollback; and an evaluation run with known limitations. Current repository status: these gates are not implemented yet.

## References

- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [LangGraph persistence guidance](https://docs.langchain.com/oss/python/langgraph/persistence)
- [MySQL account privileges](https://dev.mysql.com/doc/refman/8.4/en/privileges-provided.html)
- [Architecture and request lifecycle](architecture.md)

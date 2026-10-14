# Self-Driving Data Analyst

> Ask a business question in plain English. Get a safe, traceable analysis backed by SQL and evidence.

A portfolio project exploring a dependable natural-language analytics system with **Python, LangGraph, MySQL, and FastAPI**. SQL generation is treated as a constrained workflow: retrieve relevant metadata, propose a query, validate it, execute through read-only credentials, and explain the returned rows with provenance.

**Status: early implementation.** The repository has a LangGraph starter, typed graph state, a Gemini provider, and a first analyst node. It does **not** yet connect to a database, generate or execute SQL, expose an API, run evaluations, or implement cache/guardrail infrastructure. These are documented target capabilities, not completed features. No benchmark or production-readiness claim is made.

<p align="center"><b>Python 3.12</b> · <b>LangGraph</b> · <b>MySQL</b> · <b>FastAPI (planned)</b> · <b>Evaluation-first</b></p>

## The problem

Business users often wait for an analyst or learn SQL to answer routine data questions. LLM-generated SQL can be plausible and still be wrong, unsafe, expensive, or misleading. This project makes each step inspectable, measured, and bounded.

## End-to-end system design

The target request path is an explicit graph with validation and controlled recovery. Only the starter analyst node is implemented today.

~~~mermaid
flowchart LR
    U["Business question"] --> G["API gateway"]
    G --> A["Auth, validation, rate limits"]
    A --> I["Intent and policy check"]
    I --> S["Retrieve schema and metric context"]
    S --> P["Plan analysis"]
    P --> Q["Generate SQL"]
    Q --> V["Parse and enforce SQL policy"]
    V -->|valid| C["Authorization-scoped cache"]
    V -->|invalid| R["Bounded repair"]
    R --> Q
    C -->|hit| N["Synthesize with evidence"]
    C -->|miss| X["Read-only query runner"]
    X -->|rows or safe error| N
    N --> O["Answer, SQL, sources, trace"]
~~~

See [Architecture](docs/architecture.md) for the graph contract, state, data boundaries, failure paths, and scaling decisions.

## Engineering goals

| Concern | Target control |
| --- | --- |
| SQL safety | Read-only database principal, parsed-query allowlist, one statement, schema allowlist, row and time limits |
| Correctness | Schema and metric retrieval, deterministic validation, bounded repair, evidence-based synthesis |
| Quality | Versioned question/SQL dataset, execution and result checks, safety tests, latency and cost reporting |
| Reliability | Deadlines, bounded retries, structured errors, circuit breaker, idempotent request tracking |
| Cost and latency | Exact-result cache with authorization-aware keys, prompt/context budgets, measured model routing |
| Privacy | Secret management, PII-aware logs, retention limits, least privilege |
| Operability | Correlated traces, node-level latency, token/query metrics, redacted audit events |

These are design goals, not claims of implementation. Read [Security and reliability](docs/security-and-reliability.md), [Evaluation plan](docs/evaluation.md), and [Operations](docs/operations.md).

## Current implementation

- LangGraph StateGraph scaffold with an analyst node.
- Typed investigation state and a Gemini provider factory.
- Environment-based API key loading.

**Known gaps:** settings are loaded at import time and the graph currently asks the model for a short investigative response. There is no SQL generation, MySQL connection, FastAPI service, cache, SQL guardrail, automated test suite, tracing, or evaluation dataset yet.

## Repository map

~~~text
All_agents_tutorial/
  agent/
    graph.py                 # Current LangGraph starter
    graphstate.py            # Current graph state
    nodes/analyst_node.py    # Current LLM analyst node
    provider/factory.py      # Current Gemini provider
docs/
  architecture.md
  security-and-reliability.md
  evaluation.md
  operations.md
ROADMAP.md
~~~

## Run the current starter

Requires Python 3.12 and a Gemini API key.

~~~bash
git clone https://github.com/Durgesh9871/ai-practice-projects.git
cd ai-practice-projects/All_agents_tutorial
python -m venv .venv
# Activate the environment for your shell, then:
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY to .env
python -m agent.graph
~~~

The current node returns an LLM response to the investigation prompt; it does not query data. Dependency cleanup and reproducible installation are roadmap items.

## Delivery sequence

1. **Data foundation:** define a documented business dataset and local MySQL schema.
2. **Safe query core:** add schema discovery, SQL parsing and policy checks, read-only execution, and deterministic tests.
3. **LangGraph workflow:** add planning, generation, validation, bounded repair, and evidence-grounded synthesis.
4. **Quality loop:** create a representative evaluation set and report accuracy, safety, latency, and cost before tuning.
5. **Service and operations:** expose the graph through FastAPI, add auth/rate limits, tracing, scoped caching, and runbooks.

See the [full roadmap](ROADMAP.md) for milestones and acceptance criteria.

## Design references

Patterns were compared against public projects and primary documentation:

- [LangGraph SQL agent guide](https://docs.langchain.com/oss/python/langgraph/sql-agent) — explicit SQL workflow composition.
- [Text-to-SQL Evaluation Harness](https://github.com/AnuttaraR/text-to-sql-eval-harness) — benchmark reporting and database-boundary guardrails.
- [Portfolio_RAG](https://github.com/benwalkerai/Portfolio_RAG) — citations, tests, and reproducible setup.
- [Text-to-SQL with LangGraph and MCP](https://github.com/sktrinh12/text-to-sql) — schema-aware validation and bounded correction.
- [IBM Text2SQL Evaluation Toolkit](https://github.com/IBM/text2sql-eval-toolkit) — execution-based metrics and error analysis.

These references inform the design; their features and results are not attributed to this project.

## Principles

- The model proposes SQL; deterministic code decides whether it may run.
- Database permissions remain the final safety boundary.
- Answers distinguish returned evidence from model interpretation.
- Retries, rows, tokens, query time, and cache lifetime are bounded.
- Quality numbers are published only after a reproducible evaluation run.
- Changes stay incremental, testable, and accurately described.

## License

No license has been added yet, so reuse rights are not explicitly granted.

# OpsPilot — AI Incident Response Assistant

> **AI-assisted incident investigation for production operations teams**

OpsPilot is an AI-powered incident response assistant designed to help L2/L3 support and SRE teams investigate production incidents faster and with better traceability.

The project simulates the operational environment of **AcmePay**, a fictional fintech platform.

When an incident occurs, responders typically need to correlate several sources of information:

* previous incidents
* incident symptoms
* recent deployments
* deployment timing
* runbooks and operational knowledge
* previous resolutions

OpsPilot brings these signals together into an evidence package, uses an LLM to reason over that evidence, and produces a diagnosis and recommended actions that remain subject to **human validation**.

---

## Problem

During production incidents, the main difficulty is often not detecting the problem.

The difficult part is answering:

> **"Have we seen this before, what changed, and what should we do next?"**

A responder may need to manually search through historical incidents, compare symptoms, check recent deployments, inspect timelines and decide whether previous resolutions are relevant.

This creates several operational problems:

* investigation time increases
* useful historical knowledge is difficult to retrieve
* responders may miss relevant previous incidents
* AI-generated conclusions can be difficult to audit
* recommendations may be presented without sufficient evidence

OpsPilot addresses this by turning incident investigation into an explicit evidence-driven workflow.

---

## Solution

The MVP implements the following pipeline:

```text
Incident input
      │
      ▼
Historical incident retrieval
      │
      ▼
Deployment correlation
      │
      ▼
Evidence package
      │
      ▼
LLM reasoning
      │
      ▼
Diagnosis validation
      │
      ├───────────────┐
      │               │
      ▼               ▼
High confidence   Human validation
      │
      ▼
Recommended actions
      │
      ▼
Audit history
```

The central design principle is:

> **Deterministic code retrieves and correlates evidence. The LLM reasons only over that evidence.**

This deliberately limits the role of the LLM.

The model is not responsible for discovering arbitrary facts about the environment. It receives a structured evidence package and must produce a structured diagnosis.

---

## Example

Consider a new `payment-api` incident:

```text
Service: payment-api
Severity: SEV-1

Symptoms:
- HTTP 5xx
- database connection timeouts

Recent deployment:
- version 2.14.3
```

OpsPilot retrieves similar historical incidents:

```text
INC-0500  similarity=0.943  confirmed
INC-0505  similarity=0.943  unknown
INC-0510  similarity=0.943  confirmed
```

It also identifies a deployment shortly before the incident:

```text
DEP-001
Version: 2.14.3
Status: success
Temporal correlation: 14 minutes
```

The evidence package therefore contains both:

```text
Historical evidence
        +
Deployment evidence
        ↓
LLM diagnosis
```

The resulting diagnosis can identify:

```text
Database connection pool exhaustion
due to an N+1 query in the new release
```

and recommend:

```text
Roll back deployment 2.14.3
```

The recommendation contains explicit evidence identifiers so the operator can inspect why it was produced.

---

## Evidence-first architecture

A key design decision was to separate **evidence collection** from **reasoning**.

### Retrieval

Historical incidents are ranked using deterministic signals:

* service
* incident category
* symptom overlap
* title similarity

Importantly, the historical `root_cause` is **not** used during retrieval.

This avoids leaking the answer into the retrieval stage.

### Deployment correlation

Deployments are correlated using:

* service
* deployment timestamp
* incident timestamp
* configurable time window

For example:

```text
Deployment
    │
    │ +14 minutes
    ▼
Incident
```

The system reports this as a **temporal correlation**.

It does not claim that the deployment caused the incident.

### Evidence package

The retrieved information is transformed into a structured evidence package before reaching the LLM.

This provides a clear boundary between:

```text
System facts
      ↓
Evidence
      ↓
LLM reasoning
```

### LLM reasoning

The LLM receives only the evidence package.

The prompt explicitly requires:

* no invented facts
* no assumptions outside the evidence
* structured JSON output
* confidence score
* concise reasoning

The response is then validated against a Pydantic schema.

---

## Human-in-the-loop

OpsPilot does not automatically execute production changes.

The workflow distinguishes between:

```text
AI diagnosis
      ↓
Confidence threshold
      ↓
Recommendation
      ↓
Human validation
```

Low-confidence diagnoses are routed to human validation.

Recommendations can also be explicitly approved or rejected by an operator.

Each validation is recorded with:

* validation status
* operator
* timestamp
* optional comment

This makes the system suitable for operational environments where AI recommendations must remain auditable.

---

## Auditability

Every analysis receives a unique `request_id`.

The system stores:

* incident ID
* diagnosis
* recommended actions
* evidence
* analysis duration
* validation status
* validating operator
* validation timestamp
* validation comment

Example:

```text
request_id: 7f...
incident_id: CURRENT-001

diagnosis:
  confidence: 0.90

validation:
  status: approved
  validated_by: operator-01
```

The audit history is currently persisted as JSON for the MVP.

A production implementation could replace this repository with PostgreSQL or another durable datastore without changing the higher-level workflow.

---

## Observability

OpsPilot measures the main stages of the investigation pipeline:

```text
Retrieval
    ↓
Correlation
    ↓
Evidence construction
    ↓
LLM reasoning
    ↓
Recommendation generation
```

For each analysis, the system can capture:

* number of retrieved incidents
* number of correlated deployments
* retrieval duration
* correlation duration
* evidence construction duration
* LLM duration
* recommendation duration
* total analysis duration

This makes the system observable and provides a foundation for future performance optimization.

---

## Architecture

```text
                         ┌──────────────────────┐
                         │      Streamlit       │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │         API          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     LangGraph        │
                         │   Incident workflow  │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐      ┌──────────────┐      ┌─────────────┐
       │  Retrieval  │      │ Deployment   │      │  Evidence   │
       │             │      │ Correlation  │      │   Builder   │
       └─────────────┘      └──────────────┘      └──────┬──────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │   Gemini    │
                                                  │     LLM     │
                                                  └──────┬──────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │Recommendation│
                                                  │   Engine     │
                                                  └──────┬──────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │ Audit /     │
                                                  │ Validation  │
                                                  └─────────────┘
```

---

## Technology stack

### Backend

* Python 3.13
* FastAPI
* Pydantic
* LangGraph
* LangChain
* Google Gemini

### Frontend

* Streamlit

### Testing

* pytest

### Infrastructure

* Docker
* Docker Compose

### Data

Synthetic AcmePay operational data:

* historical incidents
* deployments
* logs
* runbooks

---

## Project structure

```text
opspilot/
│
├── app/
│   ├── api/
│   │   └── routes.py
│   │
│   ├── core/
│   │   ├── retrieval.py
│   │   ├── correlation.py
│   │   ├── evidence.py
│   │   ├── reasoning.py
│   │   ├── recommendations.py
│   │   ├── graph.py
│   │   ├── container.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── observability.py
│   │
│   ├── models/
│   │   ├── schemas.py
│   │   ├── state.py
│   │   ├── responses.py
│   │   └── audit.py
│   │
│   ├── repositories/
│   │   ├── incidents.py
│   │   ├── deployments.py
│   │   └── analyses.py
│   │
│   └── main.py
│
├── acmepay_dataset/
│   ├── incidents.json
│   ├── deployments.json
│   ├── logs/
│   └── runbooks/
│
├── frontend/
│   ├── app.py
│   └── Dockerfile
│
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── poetry.lock
└── README.md
```

---

## Running locally

### Requirements

* Python 3.13
* Poetry
* Docker Desktop
* Google Gemini API key

### Environment

Create a `.env` file:

```env
GOOGLE_API_KEY=your_gemini_api_key
OPSPILOT_GEMINI_MODEL=gemini-2.5-flash
```

The `.env` file should never be committed to Git.

---

## Run with Docker Compose

Build the services:

```bash
docker compose build
```

Start the application:

```bash
docker compose up -d
```

The API is available on:

```text
http://localhost:8000
```

The frontend is available on:

```text
http://localhost:8501
```

Health check:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "opspilot"
}
```

---

## API

### Analyze an incident

```http
POST /incidents/analyze
```

Example request:

```json
{
  "id": "CURRENT-001",
  "service": "payment-api",
  "severity": "SEV-1",
  "timestamp": "2026-10-06T09:17:00",
  "category": "connection_pool_exhaustion",
  "title": "Payment API elevated 5xx errors",
  "symptoms": [
    "HTTP 5xx",
    "database connection timeouts"
  ],
  "recent_deployment": "2.14.3"
}
```

The API returns:

* diagnosis
* confidence
* reasoning
* recommendations
* evidence
* performance metrics
* request ID

### Retrieve analysis history

```http
GET /incidents/{incident_id}/analyses
```

### Retrieve a specific analysis

```http
GET /analyses/{request_id}
```

### Validate an analysis

```http
POST /analyses/{request_id}/validation
```

Example:

```json
{
  "status": "approved",
  "validated_by": "operator-01",
  "comment": "Rollback approved."
}
```

---

## Testing

Run the complete test suite:

```bash
pytest -q
```

The project uses unit and API-level tests covering:

* Pydantic validation
* incident retrieval
* deployment correlation
* evidence construction
* LLM response parsing
* LLM error handling
* LangGraph workflow
* recommendation generation
* API behavior
* audit persistence
* human validation
* observability

The LLM integration itself is isolated behind the reasoning component so deterministic parts of the system can be tested without requiring a live model call.

---

## Design decisions

### Why LangGraph?

The incident investigation workflow contains explicit stages and conditional paths:

```text
retrieve
   ↓
correlate
   ↓
build evidence
   ↓
reason
   ↓
validate confidence
   ├── high confidence → recommend
   └── low confidence  → human validation
```

LangGraph makes these transitions explicit and keeps the orchestration separate from the business logic.

### Why deterministic retrieval?

A purely LLM-driven retrieval strategy would make the system harder to test and audit.

Deterministic retrieval provides:

* reproducibility
* explainability
* predictable behavior
* easier debugging

### Why structured LLM output?

Free-form model responses are difficult to consume safely.

The diagnosis is therefore validated using Pydantic:

```text
root_cause: str
confidence: 0..1
reasoning: str
```

Invalid model responses become explicit application errors rather than silently propagating through the system.

### Why human validation?

Production operations involve potentially high-impact actions.

OpsPilot therefore assists the operator rather than replacing the operator.

---

## Current limitations

This is an MVP and intentionally uses a simplified synthetic environment.

Current limitations include:

* JSON repositories instead of a production database
* deterministic lexical retrieval instead of vector/semantic retrieval
* synthetic incidents and deployments
* limited deployment metadata
* no direct integration with Kubernetes
* no direct integration with observability platforms
* no automatic production remediation
* no real historical measurement of investigation time
* limited authentication and authorization

These are deliberate boundaries for the MVP rather than hidden limitations.

---

## Roadmap

### Phase 1 — MVP

* [x] Incident retrieval
* [x] Deployment correlation
* [x] Evidence package
* [x] Gemini reasoning
* [x] Confidence-based routing
* [x] Recommendations
* [x] Human validation
* [x] Audit history
* [x] API
* [x] Streamlit UI
* [x] Docker Compose
* [x] Observability metrics

### Phase 2 — Operationalization

* [ ] Time-to-First-Action benchmark
* [ ] Investigation performance dashboard
* [ ] Persistent production database
* [ ] Authentication / authorization
* [ ] Better structured logging
* [ ] Prometheus metrics
* [ ] CI/CD pipeline

### Phase 3 — Real integrations

Potential integrations:

```text
Incident Management
       │
       ├── PagerDuty / Opsgenie
       │
       ▼
OpsPilot
       │
       ├── Kubernetes
       ├── Datadog / Grafana
       ├── GitHub
       └── Runbook repository
```

The goal would be to replace the synthetic AcmePay sources with real operational systems while preserving the same evidence-first architecture.

---

## FDE perspective

OpsPilot is intentionally designed as more than an LLM demo.

The project demonstrates several concerns relevant to Forward Deployed Engineering:

### Customer problem → technical workflow

The system starts from an operational problem:

> Reduce the cognitive load and investigation time associated with production incidents.

The architecture is then built around that workflow rather than around a specific AI technology.

### Integration thinking

The architecture separates:

* incident data
* deployment data
* evidence construction
* reasoning
* recommendations
* audit

This makes future integration with customer systems possible without rewriting the entire application.

### Reliability

The system includes:

* structured schemas
* explicit failure modes
* LLM timeouts
* response validation
* confidence thresholds
* human-in-the-loop validation
* auditability

### Measurable outcomes

The system captures operational metrics that can eventually be connected to business outcomes such as:

* investigation time
* time to first action
* recommendation acceptance rate
* false recommendation rate
* operator validation rate

The next major measurement to introduce is **Time-to-First-Action**, allowing the project to move from a technical demonstration toward a measurable operational impact benchmark.

---

## What this project demonstrates

OpsPilot demonstrates an approach to deploying AI into an operational workflow while keeping deterministic systems, observability and human decision-making at the center.

The key idea is simple:

> **AI should accelerate incident investigation without becoming an unaccountable source of operational truth.**

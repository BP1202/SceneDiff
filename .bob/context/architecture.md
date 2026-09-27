# SceneDiff Architecture

## System Goal

Detect runtime behavior differences between two application states.

---

## Layers

Frontend

- Dashboard
- Diff Viewer
- Report Viewer

API

- Validation
- Serialization
- Session orchestration

Services

- Scan lifecycle
- Comparison workflow
- Report generation

Behavior Engine

- Screenshot diff
- DOM diff
- Network diff
- Console diff

Secret Shield

- Secret masking
- Artifact sanitization

Storage

- Reports
- Traces
- Screenshots

Database

- Sessions
- Findings
- Reports

---

## Ownership Rules

Routes never contain business logic.

Services coordinate workflows.

Behavior Engine produces evidence.

Database stores sanitized results only.
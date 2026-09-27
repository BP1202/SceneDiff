# SceneDiff Repository Constitution

SceneDiff is an AI-powered developer workflow platform built for IBM Bob 2.0.

Mission:
Turn Git code changes into behavior changes, locate the first meaningful runtime divergence, protect developer secrets during trace collection, and help IBM Bob repair and verify regressions.

---

## Repository Values

- Security by default.
- Privacy before observability.
- Behavior over screenshots.
- Evidence over assumptions.
- Production-quality engineering.

---

## Architecture

Frontend
↓
API
↓
Behavior Engine
↓
Secret Shield
↓
Trace Store
↓
Database

Each layer owns one responsibility.

---

## AI Usage

IBM Bob is the primary engineering agent.

Bob is used for:

- Repository analysis.
- Multi-file debugging.
- Parallel investigation.
- Repair generation.
- Test generation.
- Documentation.

Never use AI for authentication, authorization, validation, or secret handling.

---

## Development Workflow

Analyze → Plan → RED → GREEN → REFACTOR → Security Review → Validation → Documentation

Never skip validation.

---

## Branch Workflow

main
↓
dev
↓
feat/*
↓
PR
↓
dev
↓
main

Never commit directly to main.

---

## Testing

Every feature must include:

- Unit tests.
- Integration tests.
- Regression tests.

---

## Security

Secret Shield runs before traces are stored.

Never store:

- API Keys
- OAuth Tokens
- JWT Secrets
- AWS Keys
- Azure Keys
- GCP Keys
- GitHub Tokens
- IBM Cloud Keys
- SSH Keys
- Cookies
- Session Tokens

Secrets are masked before persistence.

---

## Golden Rules

1. Read existing code before editing.
2. Keep changes isolated.
3. Never fabricate runtime evidence.
4. Never expose secrets in logs or traces.
5. Prefer deterministic logic over AI.
6. Every behavior difference must include evidence.
7. Every repair must be verified.
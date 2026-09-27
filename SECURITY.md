# SceneDiff Security Constitution

SceneDiff captures runtime behavior, not secrets.

---

## Secret Shield

Secret Shield executes before any trace is written.

Pipeline:

Capture
→ Detect Secrets
→ Mask Secrets
→ Validate Trace
→ Store Trace

---

## Never Persist

- AWS Access Keys
- IBM Cloud API Keys
- Gemini API Keys
- OpenAI API Keys
- Anthropic Keys
- GitHub Tokens
- Slack Tokens
- Stripe Secrets
- JWT Secrets
- OAuth Tokens
- Cookies
- Authorization Headers
- SSH Private Keys

---

## Allow Local Development Values

Allowed examples:

- POSTGRES_USER
- POSTGRES_PASSWORD
- DB_HOST=localhost
- DB_PORT=5432
- REDIS_PORT
- PLAYWRIGHT_BASE_URL=http://localhost

Local-only secrets never leave localhost.

---

## Trace Privacy Levels

PUBLIC
Safe for repository.

LOCAL_ONLY
Stored only on developer machine.

MASKED
Stored with partial masking.

BLOCKED
Trace rejected entirely.

---

## Security Rules

- Never upload .env.
- Never log Authorization headers.
- Never store cookies.
- Never store bearer tokens.
- Never store request bodies containing secrets.
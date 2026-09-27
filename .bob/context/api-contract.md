# SceneDiff API Contract

API version:

/api/v1

---

## Response Format

Every endpoint returns:

- success
- data
- error
- metadata

---

## Status Rules

Success

200 / 201

Client Error

400 / 404 / 422

Server Error

500

---

## Endpoint Rules

Routes validate requests only.

Services generate responses.

ORM models never leave API responses.

---

## Error Schema

Every error includes:

- code
- message
- request_id

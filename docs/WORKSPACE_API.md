# Investigation Workspace API

The workspace stores analyst-created cases and alerts in `data/workspace.db` (SQLite). The database is created automatically on first workspace request. No sample records are seeded.

## Cases

- `GET /workspace/cases` — list saved cases; optional `?status=open|in_review|closed`.
- `POST /workspace/cases` — create a case. Required fields: `title`, `dataset` (`elliptic`, `card_fraud`, `other`), `entity_ref`; optional `priority` (`low`, `medium`, `high`, `critical`) and `summary`.
- `PATCH /workspace/cases/{case_id}` — update `status`, `priority`, and/or `summary`.

## Alerts

- `GET /workspace/alerts` — list saved alerts; optional status filter.
- `POST /workspace/alerts` — save a score-backed alert. Requires `title`, dataset, entity reference, risk band, score in [0,1], score type, and non-empty provenance. The UI offers this only after a scoring endpoint successfully returns a valid model score.
- `PATCH /workspace/alerts/{alert_id}` — update status, notes, and optionally link a case.

Alert statuses: `new`, `reviewing`, `dismissed`, `escalated`.

## Reports

- `GET /workspace/reports/summary` — saved-case and alert breakdowns plus recent records.
- `GET /workspace/reports/evaluations` — reports whether training pipelines have created evaluation JSON artifacts; returns actual file contents only when present and readable.
- `GET /workspace/reports/export.csv` — downloads saved cases and alerts as CSV.
- `GET /workspace/reports/export.json` — JSON summary.

## Limitations

This is a local research prototype, not a production case management system. It has no authentication, authorization, multi-user access control, audit-grade tamper protection, encryption-at-rest controls, or retention policy. Do not place sensitive customer data in it or expose it to a public network. Model scores and graph connections are research signals, not proof of wrongdoing. Card-fraud scores are not AML scores.

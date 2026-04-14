# CLAUDE.md — banxe-training-data
# BANXE AI Bank — Training Data Pipeline

## Purpose

This repo ingests raw documents/data files and builds a knowledge base
consumed by BANXE AI agents (MiroFish, AML, fraud detection, risk modeling).

## Data Flow

```
raw/{docs|data|media|links}/  → ingest_processor.py → processed/ + knowledge-base/index.json
                                                     → GitHub event → developer-core → downstream repos
```

## Quality gate

```bash
make quality-gate
```

Runs: ruff lint → pytest (schema validation + data quality tests) → secrets scan

## Editing rules

- NEVER commit real customer data to raw/ (GDPR Art. 5)
- All raw files must be anonymised/synthetic before ingestion
- Schema changes require a version bump in `knowledge-base/index.json`
- Failure notifications: add Slack/email alerts to ingest.yml on failure

## CI workflow

- `ingest.yml` — triggers on push to `raw/`, auto-processes and commits results
- `ci.yml` — runs on all pushes: lint + tests + secrets scan

## Schema versioning

`knowledge-base/index.json` version field format: `MAJOR.MINOR`
- MINOR bump: new fields added (backwards-compatible)
- MAJOR bump: structural changes (coordinate with downstream consumers)

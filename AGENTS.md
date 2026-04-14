# AGENTS.md — banxe-training-data

**Repository:** `~/banxe-training-data/`
**Version:** 1.0 | 2026-04-12
**Purpose:** BANXE AI training data pipeline (AML/KYC compliance corpus)
**Stack:** Python 3.11+, ruff, pytest

---

## Core mission

Training data pipeline for BANXE compliance AI models.
Ingests, processes, validates, and exports labelled AML/KYC datasets.

---

## Four-Partner Swarm

| # | Partner | Role |
|---|---------|------|
| 1 | **Claude Code** | Data schema design, pipeline architecture |
| 2 | **Aider CLI** | Pipeline script executor |
| 3 | **MiroFish** | Scenario-based data generation |

---

## Instruction hierarchy

1. Explicit user instruction
2. `CLAUDE.md` — data pipeline context
3. `AGENTS.md` — this file
4. `~/.claude/CLAUDE.md` — global defaults

---

## Data pipeline stages

```
raw/            ← Source data (never commit PII)
processed/      ← Cleaned, anonymised, labelled
knowledge-base/ ← Vectorised for RAG
```

---

## Critical rules

| Rule | Details |
|------|---------|
| **PII** | Never commit real PII — always anonymise before ingest |
| **Labelling** | AML labels require compliance officer review |
| **Versioning** | Dataset versions in `processed/vX.Y/` |

---

## Development commands

```bash
pip install -r requirements-dev.txt
pytest tests/
ruff check .
make quality-gate
pre-commit run --all-files
```

---

## Repository structure

```
banxe-training-data/
├── raw/            ← Source data (gitignored)
├── processed/      ← Clean training datasets
├── knowledge-base/ ← RAG knowledge base
├── tests/          ← Data validation tests
└── Makefile        ← Pipeline commands
```

---

## Definition of done

- [ ] PII scan passes (no real data committed)
- [ ] `pytest tests/` green
- [ ] `ruff check .` clean
- [ ] Dataset version tagged

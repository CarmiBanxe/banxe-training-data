# ArchiMate Registry — archimate-map.md
<!-- 13th registry for banxe-emi-stack | Source: archimate/banxe-model.xml -->
<!-- AUTO-SYNC: run `make import-archimate` after Archi export -->

## Purpose
Maps ArchiMate enterprise architecture model (Archi Tool) to banxe-emi-stack code.
AI agents use this registry to understand which code modules implement which architecture components.

**Model stats:** 44 elements · 37 relationships · 5 views

## Application Layer

| Element Name | ArchiMate Type | Banxe Domain | Module/Host | Status |
|-------------|---------------|-------------|------------|--------|
| AML / Fraud Service | ApplicationComponent | services | `services/fraud/` | ACTIVE |
| API Gateway | ApplicationComponent | services | `api/main.py` | ACTIVE |
| Auto-Verify API | ApplicationComponent | services | `localhost:8094` | ACTIVE |
| Banxe Screener | ApplicationComponent | services | `localhost:8085` | ACTIVE |
| Deep Search | ApplicationComponent | services | `localhost:8088` | ACTIVE |
| Hyperswitch App Server | ApplicationComponent | services | `localhost:8096` | ACTIVE+P0 |
| Hyperswitch Card Vault | ApplicationComponent | services | `localhost:8098` | ACTIVE+P0 |
| Hyperswitch Control Center | ApplicationComponent | services | `localhost:8097` | ACTIVE |
| IAM Service | ApplicationComponent | services | `services/iam/` | ACTIVE |
| KYC Service | ApplicationComponent | services | `services/kyc/` | ACTIVE |
| Ledger Service | ApplicationComponent | services | `services/ledger/` | ACTIVE |
| OpenClaw ctio-bot | ApplicationComponent | services | `localhost:18791` | ACTIVE |
| OpenClaw moa-bot | ApplicationComponent | services | `localhost:18789` | ACTIVE |
| PII Proxy / Presidio | ApplicationComponent | services | `localhost:8089` | ACTIVE |
| Payment Service | ApplicationComponent | services | `services/payment/` | ACTIVE+STUB |
| Safeguarding Service | ApplicationComponent | services | `src/safeguarding/` | ACTIVE |
| Tri-Party Reconciliation Engine | ApplicationComponent | services | `src/settlement/reconciler_engine.py` | ACTIVE |
| Yente / OpenSanctions | ApplicationComponent | services | `localhost:8086` | PLANNED |

## Business Process Layer

| Element Name | ArchiMate Type | Banxe Domain | Module/Host | Status |
|-------------|---------------|-------------|------------|--------|
| Consumer Duty DISP | BusinessProcess | workflows | `—` | — |
| Customer Onboarding | BusinessProcess | workflows | `—` | — |
| Daily Reconciliation | BusinessProcess | workflows | `—` | — |
| FIN060 Return | BusinessProcess | workflows | `—` | — |
| Payment Processing | BusinessProcess | workflows | `—` | — |
| SAR Filing | BusinessProcess | workflows | `—` | — |
| Sanctions Screening | BusinessProcess | workflows | `—` | — |
| Transaction Monitoring | BusinessProcess | workflows | `—` | — |

## Technology Layer

| Element Name | ArchiMate Type | Banxe Domain | Module/Host | Status |
|-------------|---------------|-------------|------------|--------|
| ClickHouse Audit DB | TechnologyService | infrastructure | `localhost:8123` | — |
| Firebase Emulator | TechnologyService | infrastructure | `localhost:9099` | ACTIVE |
| Jube TM | TechnologyService | infrastructure | `localhost:5001` | ACTIVE |
| Keycloak IAM | TechnologyService | infrastructure | `localhost:8180` | — |
| Marble Case Management | TechnologyService | infrastructure | `localhost:5002` | — |
| Midaz CBS | TechnologyService | infrastructure | `localhost:8095` | — |
| MongoDB (Midaz) | TechnologyService | infrastructure | `localhost:5703` | ACTIVE |
| Ollama | TechnologyService | infrastructure | `localhost:11434` | ACTIVE |
| PostgreSQL (Jube) | TechnologyService | infrastructure | `localhost:15432` | ACTIVE |
| PostgreSQL (Marble) | TechnologyService | infrastructure | `localhost:15433` | ACTIVE |
| PostgreSQL (compliance) | TechnologyService | infrastructure | `localhost:5432` | ACTIVE |
| RabbitMQ (Midaz) | TechnologyService | infrastructure | `localhost:3003/3004` | ACTIVE |
| Redis | TechnologyService | infrastructure | `localhost:6379` | ACTIVE |
| Redis (Jube) | TechnologyService | infrastructure | `localhost:16379` | ACTIVE |
| n8n | TechnologyService | infrastructure | `localhost:5678` | ACTIVE |
| nginx | TechnologyService | infrastructure | `localhost:443/80` | ACTIVE |

## Data Objects

| Element Name | ArchiMate Type | Banxe Domain | Module/Host | Status |
|-------------|---------------|-------------|------------|--------|
| CustomerProfile | DataObject | models | `api/models/customers.py` | — |
| TransactionRecord | DataObject | models | `services/ledger/midaz_adapter.py` | — |

## Relationships Summary

| Relationship Type | Count |
|------------------|-------|
| Serving | 19 |
| Access | 8 |
| Composition | 6 |
| Flow | 4 |

## Views (Diagrams)

| View Name | Nodes |
|-----------|-------|
| Application Layer — Banxe EMI Stack | 6 |
| CASS 15 Safeguarding Architecture | 4 |
| Compliance & AML Stack | 6 |
| Payment Stack — Hyperswitch | 4 |
| Ledger Stack — Midaz CBS | 4 |

## Sync Instructions
1. Export from Archi: File → Export → Open Exchange XML → archimate/banxe-model.xml
2. Run: `make import-archimate`
3. This file auto-updates via `--generate-registry`
4. Commit changes to banxe-architecture

<!-- Generated by scripts/import_archimate.py --generate-registry -->
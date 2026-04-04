# MEMORY.md — Banxe AI Bank

> Последнее обновление: 2026-04-03. Phase 2b Marble deployed. Роутинг агентов → см. AGENTS.md

## Инфраструктура

- **Legion Pro 5** (i7-14700HX, 16GB) — терминал, WSL2 Ubuntu 24.04
- **GMKtec EVO-X2** (Ryzen AI MAX+ 395, 128GB RAM) — AI мозг
- SSH: `ssh gmktec` (порт 2222, алиас настроен)

## Люди

- CEO: Moriel Carmi (Mark) — @bereg2022, ID: 508602494
- CTIO: Олег — @p314pm, user `ctio` на GMKtec (права = CEO)

## Сервисы GMKtec

| Сервис | Порт | Статус |
|---|---|---|
| Ollama | 11434 | active |
| OpenClaw moa-bot | 18789 | active |
| OpenClaw ctio-bot | 18791 | active |
| OpenClaw @mycarmibot | 18793 | active |
| ClickHouse | 9000 | active |
| PII Proxy (Presidio) | 8089 | active |
| Deep Search | 8088 | active |
| n8n | 5678 | active |
| nginx | 443/80 | active |
| Jube TM | 5001 | active |
| Marble API | 5002 | active |
| Marble UI | 5003 | active |

## Ollama модели (актуально 2026-04-03)

- **qwen3-banxe-v2** — ГЛАВНАЯ МОДЕЛЬ (main/supervisor/kyc/compliance/risk/crypto). Создана из qwen3:30b-a3b с пустым think-блоком для подавления reasoning.
- glm-4.7-flash-abliterated — client-service/operations/it-devops
- gpt-oss-derestricted:20b — analytics/finance
- УДАЛЕНЫ: qwen3.5-abliterated:35b (no tools), llama3.3:70b (медленный)
- Thinking подавлено: пустой `<think></think>` в Modelfile template (НЕ через params)
- OLLAMA_KEEP_ALIVE=-1 (модель всегда в памяти, нет cold start)

## Боты

- @mycarmi_moa_bot → порт 18789, конфиг /root/.openclaw-moa/.openclaw/openclaw.json
- Workspace moa: /home/mmber/.openclaw/workspace-moa/
- @mycarmibot → порт 18793 (не трогать)

## ClickHouse

- БД: banxe, 6 таблиц
- KYC webhook: POST /webhook/kyc-onboard
- AML webhook: POST /webhook/aml-check

## Cron (GMKtec)

- memory-autosync-watcher.sh (docs/MEMORY.md → workspace, каждые 5 мин + **SOUL GUARD**)
- ctio-watcher.sh v2 (сервер → SYSTEM-STATE.md → GitHub)
- watchdog-watcher.sh (каждые 15 мин)
- backup-clickhouse.sh (каждые 6 ч)

## SOUL.md Protection (IMPLEMENTED 2026-04-04)

- **Проблема**: OpenClaw перезаписывал `/root/.openclaw-moa/workspace-moa/SOUL.md` при рестарте
- **Canonical source**: `/root/.openclaw-moa/soul-protected/SOUL.md` (3086 bytes, compliance version)
- **Защита Уровень 1**: `chattr +i` на обоих workspace SOUL.md (root + mmber)
- **Защита Уровень 2**: SOUL GUARD в memory-autosync-watcher.sh — hash-check + авторестор каждые 5 мин
- **Управление**: `scripts/protect-soul.sh` (deploy / update / unlock / status)
- **Обновить SOUL.md**: `git pull && bash scripts/protect-soul.sh update /data/vibe-coding/docs/SOUL.md`
- **Полный runbook**: `docs/SOUL-PROTECTION.md`

## Санкционная политика Banxe (UK FCA EMI, 2026)

### Категория A — HARD BLOCK (REJECT одной строкой)
Россия/РФ, Беларусь, Иран, КНДР/Северная Корея, Куба, Мьянма, Афганистан, Венесуэла (гос.), Крым, ДНР, ЛНР

### Категория B — EDD/HOLD (Extended Due Diligence)
Сирия (⚠️ снята с BLOCK июль 2025 — санкции Assad частично сняты), Ирак, Ливан, Йемен, Гаити, Мали, Буркина-Фасо, Нигер, Судан, Ливия, Сомали, ДР Конго, ЦАР, Зимбабве, Никарагуа, Южный Судан

### НЕ заблокированы (стандартный AML)
Южная Корея, ОАЭ, Япония, Израиль, Турция, Индия, Бразилия, Мексика, США, EU (все), UK

### Шаблон ответа (СТРОГО — не отклоняться)

**ФОРМАТ ОТВЕТА — только это, ничего лишнего:**
[Страна/транзакция] → [СТАТУС]: [одна строка причины]

**Примеры правильных ответов:**
- Россия → REJECT: заблокированная юрисдикция.
- Сирия → HOLD: EDD-юрисдикция, усиленная проверка.
- Южная Корея £50,000 → HOLD: сумма >£10k, EDD обязателен.
- Южная Корея £500 → ALLOW: низкий риск, стандартный AML.

**ЗАПРЕЩЕНО в ответах:**
- Эмодзи любые (флаги стран, галочки, ракеты и т.д.)
- Таблицы
- Разделители (───)
- Вопросы в конце ("Готовы ли вы...?")
- Упоминание ClickHouse, SumSub, LexisNexis, Dow Jones (не подключены)
- Обращение "Привет, Mark!" — отвечать сразу по существу

**ВАЖНО:** Категория B (Сирия, Ирак, Ливан и др.) = HOLD, НЕ REJECT.

## Задачи

- DONE: Security hardening, GTT unlock (59392MB), ROCm, qwen3:30b-a3b, Sanctions policy, Verification env, SOUL.md deployment (chattr +i + soul-protected + SOUL GUARD в autosync)
- PENDING: CTIO бот (ждём token), Vendor API, HITL Dashboard
- КРИТИЧНО: think:false через params — проверить что OpenClaw передаёт в Ollama API

## Compliance Stack (src/compliance/)

Исходный код AML/KYC стека теперь в репозитории vibe-coding: `src/compliance/`
Задеплоен на GMKtec: `/data/banxe/compliance/`
Локальная копия (collaboration): `/home/mmber/collaboration/compliance/` — более не основная

| Файл | Назначение |
|------|-----------|
| api.py | FastAPI :8090 — 9 endpoints |
| audit_trail.py | ClickHouse logging, TTL 5 лет |
| crypto_aml.py | FINOS OpenAML + Watchman OFAC |
| dashboard.py | CEO Dashboard, ClickHouse analytics |
| sanctions_check.py | Watchman + finsanctions |
| test_suite.py | 20 тестов, 18 pass, 2 warn |
| tx_monitor.py | 6 правил + Redis velocity |



### Banxe Screener API (порт 8085)
- Watchman: http://localhost:8085/screen?q=entity_name
- sanctioned + pep + risk_level + matches
- Sources: Moov Watchman (OFAC/UN/EU/UK) + Wikidata SPARQL (PEP, CC0)

### Moov Watchman (порт 8084, Apache 2.0)
- Binary: /usr/local/bin/banxe-watchman
- Data: /data/banxe/watchman/
- Lists: OFAC SDN, UN, EU, UK OFSI, US CSL, FinCEN 311

### OpenClaw Skill
- workspace-moa/skills/banxe-screener/SKILL.md
- Agents вызывают: curl http://localhost:8085/screen?q=ИМЯ

### Phase 2a — Jube TM (2026-04-03)
- deploy-phase2-jube.sh: PostgreSQL 17 + Redis Stack + Jube WebAPI + Jube Jobs
- Jube source: /data/banxe/jube-src (AGPLv3, internal only)
- Порты: Jube API→5001, PG→15432 (internal), Redis→16379 (internal)
- OpenClaw skill: workspace-moa/skills/jube-aml/SKILL.md
- Интеграция: Jube callback → Screener /screen для обогащения кейсов

### Phase 2b — Marble Case Management (2026-04-03 DEPLOYED)
- deploy-phase2-marble.sh: marble-backend (Go) + marble-frontend (React) + PostgreSQL 17 + Firebase emulator
- Marble source: /data/banxe/marble-src (Apache 2.0)
- Порты: Marble API→5002, Marble UI→5003, PG→15433 (internal), Firebase→9099/4000
- Compose: /data/banxe/marble-src/docker-compose.marble.yml
- Organisation: Banxe (created)
- Admin user: mark@banxe.com (created)
- Auth: Firebase emulator (local mode, no cloud Firebase needed)
- OpenClaw skill: workspace-moa/skills/marble-cases/SKILL.md (TODO)
- MLRO рабочий стол: http://[gmktec]:5003

### Полный стек (после деплоя Phase 2)
```
Screener  :8085 → Watchman :8084          Phase 1
Jube TM   :5001 → SAR detection           Phase 2a
Marble    :5002 → Case management UI      Phase 2b
ClickHouse:9000 → FCA audit trail         always
```

### Phase 3 (следующий): PassportEye (MRZ) + DeepFace (liveness) — KYC documents

## Обучающий стек (Перекрёстная верификация агентов)

> Установлено: 2026-04-04

### Инструменты (GMKtec) — установлено 2026-04-04
| Инструмент | Версия | Расположение |
|---|---|---|
| Promptfoo | 0.121.3 | глобальный бинарь + npx |
| DeepEval | 3.9.5 | системный pip |
| LangGraph | 1.1.6 | системный pip |
| TinyTroupe | 0.0.1 | системный pip (--break-system-packages) |
| AMLSim | git | /opt/AMLSim |
| AMLGentex | git | /opt/AMLGentex |
| Evidently AI | 0.7.21 | системный pip |
| OpenRLHF | **0.9.10** | /root/.venvs/openrlhf (активация: source /root/.venvs/openrlhf/bin/activate) |
| flash-attn | 2.8.3 | в venv openrlhf (legacy mode — нет CUDA модуля) |

### GPU на GMKtec
- AMD Ryzen AI MAX+ 395 → **ROCm доступен**
- torch 2.11.0+cu130 (CUDA build, CUDA=False) — для ROCm нужна ROCm-сборка torch
- flash-attn установлен но работает без CUDA (legacy attention mode) — приемлемо для верификации
- Полноценный RLHF с GPU acceleration → Legion RTX 4070 (setup-openrlhf-legion.sh)

### Данные и корпус
- /data/banxe-training/ — обучающий корпус (5 категорий A-E)
- ClickHouse: banxe.verification_corpus — лог всех верификаций

### autoresearch (karpathy-style)
- Роль: вспомогательный контур R&D, НЕ продовый
- Оптимизирует: системные инструкции верификаторов, scoring, thresholds
- Установлен: /opt/AutoResearchClaw/

## Training Data Pipeline (ACTIVE 2026-04-04)

- Workflow: `.github/workflows/extract-training-data.yml`
- Целевое репо: `CarmiBanxe/banxe-training-data`
- Секрет `TRAINING_DATA_TOKEN` установлен ✅ (fine-grained PAT от CarmiBanxe)
- Corpus: A-compliance / B-architecture / C-scenarios / D-decisions / E-feedback
- Триггер: push в main, кроме `auto: SYSTEM-STATE`
- D-decisions экспорт: `scripts/backup-clickhouse-training.sh` — запускать ежемесячно на GMKtec
- Adversarial sim: `scripts/run-adversarial-sim.sh` — cron на GMKtec, воскресенье 02:00
  → экспортирует `banxe.audit_trail` → `docs/training-exports/decisions-YYYY-MM.jsonl`
  → workflow подберёт при следующем push
# workflow verified 2026-04-04T21:11:15Z

## Developer Core (~/developer → main, 2026-04-05)

- Репо: `CarmiBanxe/developer-core`, локально: `~/developer`
- Ветка: `master` → `main` (переименована, master удалена)
- ss1 добавлен в sync-targets (sync-to-project.sh + PROJECT-REGISTRY.csv)
- collaboration → developer-core: слияние завершено (commit 27bf885)
- PENDING (user browser action): архивировать `CarmiBanxe/collaboration` → Settings → Danger Zone → Archive
- Замена CodeQL: `banxe-verification-tests.yml` (LangGraph cross-verification network, 5 категорий A-E)
- Training CI: `training-quality-report.yml` (deepeval + evidently, еженедельно пн 03:00 UTC)
- BUG FIX 2026-04-05: `without EDD` / `PEP without` добавлены в forbidden patterns compliance_validator
  (было: "Approve PEP without EDD" → CONFIRMED; стало: → REFUTED confidence 1.0)
- Verify API: `banxe-verify-api.service` → порт 8094 (8091=HITL, 8092=Guiyon bridge)
  Skill: `workspace-moa/skills/verify-statement/SKILL.md`
  SOUL.md обновлены: compliance + kyc агенты
  Cron adversarial sim: /etc/cron.d/banxe-adversarial (вс 02:00)

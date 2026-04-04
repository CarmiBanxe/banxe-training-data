# banxe-training-data

Обучающий корпус для Banxe AI Bank (UK EMI, FCA authorised).

Автоматически синхронизируется из [CarmiBanxe/vibe-coding](https://github.com/CarmiBanxe/vibe-coding) через GitHub Actions при каждом push в `main`.

---

## Структура corpus

```
corpus/
├── A-compliance/     # Compliance stack: Python-модули, SQL-схемы, COMPLIANCE_ARCH.md
├── B-architecture/   # Архитектурные документы: COLLAB.md, MEMORY.md, CLAUDE.md
├── C-scenarios/      # Сценарии и паттерны: MIROFISH-SCENARIOS.md, BOT-ERROR-PATTERNS.md
├── D-decisions/      # ClickHouse audit trail export (decisions-YYYY-MM.jsonl)
├── E-feedback/       # Результаты тестов: pytest output, diagnostic-report.md
└── META.json         # Метаданные: source commit, timestamp, actor
```

## Синхронизация

Workflow: `vibe-coding/.github/workflows/extract-training-data.yml`

**Триггер**: push в `main` в `vibe-coding`, исключая коммиты `auto: SYSTEM-STATE`

**Секрет**: `TRAINING_DATA_TOKEN` в `vibe-coding` → PAT с правами `repo` (write) на этот репо

## D-decisions (ClickHouse)

Раздел заполняется через `backup-clickhouse-training.sh` на GMKtec.
Формат: `decisions-YYYY-MM.jsonl` — FCA audit trail, одна запись на строку.
Пока файлы не добавлены — workflow пропускает этот раздел без ошибки.

## Использование

Данные предназначены для fine-tuning / RLHF / RAG пайплайна Banxe AI Bank.
Репо приватное. Доступ: только `CarmiBanxe` organization.

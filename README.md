# Banxe Training Data

**Private repository** — Internal knowledge base for Banxe AI Bank  
**Version:** 1.0 | **Created:** 2026-04-03

---

## 🎯 Purpose

Централизованное хранилище обучающих данных и знаний для Banxe AI Bank:

- **Regulatory compliance** — FCA, PRA, AML/KYC документы
- **Product knowledge** — Спецификации, UX flows, architecture
- **Training materials** — Документы для обучения ML моделей
- **Market intelligence** — Конкуренты, исследования, метрики

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Олег (Banxe Team)                        │
│              push файлов в raw/ (docs/data/media)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   banxe-training-data        │
        │   GitHub Actions: ingest.yml │
        │   - PDF/DOCX → text extract  │
        │   - CSV/JSON → validate      │
        │   - Create index.json        │
        └──────────────┬───────────────┘
                       │
                       │ repository_dispatch event
                       ▼
        ┌──────────────────────────────┐
        │   developer-core             │
        │   workflow: sync-training    │
        │   - Receive event            │
        │   - Pull knowledge-base      │
        │   - Distribute to BANXE      │
        └──────────────┬───────────────┘
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌────────────┐
    │vibe-coding│ │collaboration│ │banxe-mirofish│
    │knowledge- │ │knowledge- │ │knowledge-  │
    │base/      │ │base/      │ │base/       │
    └──────────┘ └──────────┘ └────────────┘
```

---

## 📁 Structure

```
banxe-training-data/
├── raw/                    ← СЮДА ДОБАВЛЯТЬ ФАЙЛЫ
│   ├── docs/               ← PDF, DOCX, TXT, MD
│   ├── data/               ← CSV, JSON, XLSX
│   ├── media/              ← PNG, JPG, GIF, SVG
│   └── links/              ← URL lists
│
├── processed/              ← Автоматически обработанные
│   ├── docs/               ← Извлечённый текст
│   └── data/               ← Валидированные данные
│
├── knowledge-base/         ← Готовая база знаний
│   ├── index.json          ← Полный индекс всех материалов
│   └── README.md           ← Человекочитаемое описание
│
├── scripts/
│   └── ingest_processor.py ← Локальная обработка
│
├── .github/workflows/
│   └── ingest.yml          ← Автоматический pipeline
│
├── CONTRIBUTING.md         ← Инструкция для Олега
└── README.md               ← Этот файл
```

---

## 🚀 Quick Start (для Олега)

### 1. Добавить файлы

```bash
# Копировать в нужную папку
cp ~/Documents/fca-handbook.pdf raw/docs/
cp ~/Data/transactions.csv raw/data/
cp ~/Screenshots/kyc-flow.png raw/media/
```

### 2. Закоммитить и запушить

```bash
git add raw/docs/fca-handbook.pdf raw/data/transactions.csv
git commit -m "docs: FCA Handbook + Q1 transaction metrics"
git push origin main
```

### 3. Проверить результат

Через 2-5 минут:
- Открыть вкладку **Actions** на GitHub
- Выбрать последний запуск "Ingest Training Data"
- Посмотреть summary

Готово! Knowledge-base обновлён и распространён по всем BANXE репозиториям.

---

## ⚙️ Automation

### Ingest Pipeline (`ingest.yml`)

Запускается автоматически при каждом push в `raw/`:

1. **Checkout** — забирает все файлы
2. **Install** — pymupdf, python-docx, openpyxl
3. **Process** — извлекает текст, валидирует данные
4. **Index** — создаёт `knowledge-base/index.json`
5. **Commit** — пушит processed/ и knowledge-base/
6. **Notify** — отправляет событие в developer-core

**Время выполнения:** 2-4 минуты

### Sync Workflow (`sync-training-data.yml`)

Запускается по событию `training-data-updated`:

1. **Pull** — забирает knowledge-base из banxe-training-data
2. **Commit** — обновляет developer-core/knowledge-base/
3. **Distribute** — пушит в vibe-coding, collaboration, banxe-mirofish

**Время выполнения:** 1-2 минуты

---

## 📊 Supported Formats

| Category | Extensions | Processing |
|----------|------------|------------|
| **Documents** | PDF, DOCX, TXT, MD | Text extraction (PDF/DOCX), copy (TXT/MD) |
| **Data** | CSV, JSON, XLSX | Validation + metadata |
| **Media** | PNG, JPG, GIF, SVG | Metadata extraction, copy |
| **Links** | URL lists | Parsing + categorization |

**Максимальный размер файла:** 100 MB (GitHub limit)

---

## 🔍 Using Knowledge Base

### Programmatic Access

```python
import json

# Загрузить индекс
with open('knowledge-base/index.json', 'r') as f:
    kb = json.load(f)

# Узнать сколько файлов
print(f"Total: {kb['total_files']}")

# Найти документы по категории
for doc in kb['categories']['docs']:
    print(f"- {doc['filename']} ({doc['status']})")

# Получить текст конкретного файла
for file_info in kb['files']:
    if file_info['filename'] == 'fca-handbook.pdf':
        print(file_info['extracted_text'][:500])
```

### Manual Browsing

Открыть `knowledge-base/README.md` — человекочитаемый список всех файлов с превью.

---

## 🔐 Security

### Private Repository

Этот репозиторий **PRIVATE** по умолчанию:

- Только приглашённые collaborator имеют доступ
- GitHub Actions используют secrets (SYNC_TOKEN)
- Логи workflow видны только владельцам

### Do NOT Upload

❌ **Персональные данные клиентов** (GDPR violation)
- Реальные имена, адреса, DOB
- Номера счетов, карт, паспортов

❌ **Секреты и ключи**
- API keys, passwords, credentials
- Private keys, seed phrases

❌ **Конфиденциальную информацию партнёров**
- NDA-covered documents
- Pre-release features

✅ **Можно:** публичные регуляторные документы, внутренние policy (без sensitive data), архитектурные решения.

---

## 🛠️ Local Development

### Запустить ingest локально

```bash
cd banxe-training-data

# Установить зависимости
pip install pymupdf python-docx openpyxl pandas

# Запустить процессор
python scripts/ingest_processor.py

# Проверить результат
cat knowledge-base/index.json
cat knowledge-base/README.md
```

### Требования

- Python 3.10+
- pymupdf (извлечение PDF)
- python-docx (извлечение DOCX)
- openpyxl (работа с XLSX)

---

## 📈 Monitoring

### GitHub Actions Status

Открыть https://github.com/CarmiBanxe/banxe-training-data/actions

Последние запуски:
- ✅ Success — всё ок
- ⚠️ Warning — частичная обработка
- ❌ Failure — ошибка, смотреть логи

### Knowledge Base Stats

```bash
# Посмотреть статистику
cat knowledge-base/index.json | python -m json.tool | head -20

# Количество файлов по категориям
python -c "import json; d=json.load(open('knowledge-base/index.json')); print('Docs:', len(d['categories']['docs'])); print('Data:', len(d['categories']['data']))"
```

---

## 🔗 Integration Points

### MiroFish Integration

Когда поступают финансовые данные от Олега:

1. MiroFish подключается к `knowledge-base/index.json`
2. Использует данные для:
   - Analytics (рыночные тренды)
   - Predictions (adoption curves)
   - Risk modeling (fraud patterns)

**Auto-trigger keywords:**
- `market data`, `metrics`, `adoption` → gtm-reaction.yml
- `fraud patterns`, `transaction data` → fraud-stress-test.yml

### Developer-Core Hub

developer-core получает событие и автоматически раздаёт knowledge-base во все BANXE проекты:

- vibe-coding → compliance training, fraud detection
- collaboration → multi-agent coordination
- banxe-mirofish → simulation scenarios

---

## 👥 Team

| Role | Person | Scope |
|------|--------|-------|
| **Content Owner** | Олег | Наполнение raw/, качество материалов |
| **Pipeline Maintainer** | @bereg2022 | ingest.yml, sync workflows |
| **Integration Lead** | Qoder CLI | MiroFish integration, distribution |

---

## 📞 Support

**Issues:** https://github.com/CarmiBanxe/banxe-training-data/issues  
**Telegram:** @p314pm (Олег)

---

## 📝 License

Internal use only — Banxe AI Bank proprietary

---

**Last Updated:** 2026-04-03  
**Next Review:** After first production batch from Олег

# CONTRIBUTING.md — Инструкция по наполнению Banxe Training Data

**Для:** Олег (и команда Banxe)  
**Цель:** Автоматическое создание knowledge-base из ваших материалов

---

## 🎯 Как это работает

```
Олег push в raw/ → GitHub Actions обрабатывает → knowledge-base готов
                                            ↓
                              developer-core получает уведомление
                                            ↓
                              vibe-coding, collaboration, banxe-mirofish
```

Полная цепочка занимает **2-5 минут**.

---

## 📁 Структура папок

```
banxe-training-data/
├── raw/                    ← СЮДА КИДАТЬ ФАЙЛЫ
│   ├── docs/               ← PDF, DOCX, TXT, MD (документы)
│   ├── data/               ← CSV, JSON, XLSX (данные)
│   ├── media/              ← PNG, JPG (скриншоты, схемы)
│   └── links/              ← URL с описаниями
├── processed/              ← Автоматически обработанные файлы
└── knowledge-base/         ← Готовая база знаний (index.json)
```

---

## ✅ Что можно загружать

### 1. Документы (`raw/docs/`)

| Формат | Обработка | Результат |
|--------|-----------|-----------|
| **PDF** | Извлечение текста | `.txt` + текст в index.json |
| **DOCX** | Извлечение текста | `.txt` + текст в index.json |
| **TXT** | Копирование | Как есть + превью в index.json |
| **MD** | Копирование | Как есть + превью в index.json |

**Примеры:**
- Compliance документация (FCA Handbook, PRA Rulebook)
- Внутренние политики Banxe
- Технические спецификации
- Юридические документы

### 2. Данные (`raw/data/`)

| Формат | Обработка | Результат |
|--------|-----------|-----------|
| **CSV** | Копирование + валидация | Как есть + метаданные |
| **JSON** | Парсинг + индексация | Структурированный индекс |
| **XLSX** | Копирование | Как есть + первый лист в index.json |

**Примеры:**
- Санкционные списки (OFAC, HMT)
- Транзакционные данные (анонимизированные)
- Пользовательские метрики
- Рыночные данные

### 3. Медиа (`raw/media/`)

| Формат | Обработка | Результат |
|--------|-----------|-----------|
| **PNG, JPG** | Метаданные | Копия + описание в index.json |
| **SVG** | Копирование | Вектор как есть |

**Примеры:**
- Скриншоты UI/UX
- Архитектурные диаграммы
- Блок-схемы процессов

### 4. Ссылки (`raw/links/`)

Создайте текстовый файл со списком URL:

```text
# compliance-sources.txt
https://www.handbook.fca.org.uk/handbook/TCB/
— FCA Training and Competence Sourcebook

https://www.jmlsg.org.uk/guidance
— Joint Money Laundering Steering Group

https://ofac.treasury.gov/sanctions-list-service
— OFAC Sanctions List (XML API)
```

---

## 🚀 Пошаговая инструкция

### Шаг 1: Подготовка файлов

**На компьютере:**
```bash
# Создайте локальную копию репозитория
git clone https://github.com/CarmiBanxe/banxe-training-data.git
cd banxe-training-data
```

### Шаг 2: Добавление материалов

**Копируйте файлы в соответствующие папки:**

```bash
# Документы
cp ~/Downloads/fca-handbook.pdf raw/docs/
cp ~/Documents/banxe-policy.docx raw/docs/

# Данные
cp ~/Exports/transactions.csv raw/data/
cp ~/Exports/customers.json raw/data/

# Скриншоты
cp ~/Screenshots/ui-flow.png raw/media/

# Или через GitHub UI:
# 1. Открыть https://github.com/CarmiBanxe/banxe-training-data
# 2. Click "Add file" → "Upload files"
# 3. Перетащить файлы в нужную папку (docs/data/media)
```

### Шаг 3: Коммит и пуш

```bash
# Добавить файлы
git add raw/docs/fca-handbook.pdf
git add raw/docs/banxe-policy.docx
git add raw/data/transactions.csv

# Закоммитить с понятным сообщением
git commit -m "docs: FCA Handbook TCB source + internal policy v2.1"

# Запушить
git push origin main
```

### Шаг 4: Проверка результата

**Через 2-5 минут:**

1. Открыть вкладку **Actions** на GitHub
2. Выбрать последний запуск "Ingest Training Data"
3. Посмотреть summary:
   - Сколько файлов обработано
   - Какие категории обновлены
   - Статус отправки в developer-core

**Результат в knowledge-base:**
- `knowledge-base/index.json` — полный индекс всех материалов
- `knowledge-base/README.md` — человекочитаемое описание

---

## 📝 Примеры сообщений коммитов

```bash
# Документы
git commit -m "docs: Add FCA Compliance Sourcebook (TCB/PERG)"
git commit -m "docs: Update AML policy to v3.2 (2026 revision)"

# Данные
git commit -m "data: Q1 2026 transaction metrics (anonymized)"
git commit -m "data: OFAC sanctions list weekly update"

# Медиа
git commit -m "media: KYC onboarding flow screenshots (7 images)"

# Массовое добавление
git commit -m "init: Initial training data batch (42 files)
- docs: 15 PDF/DOCX (compliance, legal, product)
- data: 8 CSV/JSON (metrics, sanctions, users)
- media: 19 PNG (UI flows, architecture diagrams)"
```

---

## ⚠️ Важные правила

### НЕ загружать:

❌ **Персональные данные клиентов** (GDPR violation)
- Реальные имена, адреса, даты рождения
- Номера счетов, карт, паспортов
- anything identifiable

❌ **Секреты и ключи**
- API keys, passwords, credentials
- Private keys, seed phrases
- Database connection strings

❌ **Конфиденциальную информацию партнёров**
- NDA-covered documents
- Pre-release partner features
- Unpublished regulatory communications

### МОЖНО загружать:

✅ **Публичные регуляторные документы**
- FCA/PRA handbooks (publicly available)
- EU directives (MiFID II, PSD2)
- FATF guidance

✅ **Внутренние документы БЕЗ sensitive data**
- Архитектурные решения (без секретов)
- Продуктовая документация
- UX исследования (анонимизированные)

✅ **Обучающие материалы**
- Public case studies
- Industry reports
- Conference presentations

---

## 🔧 Автоматизация

### Локальная проверка перед push

```bash
# Запустить ingest processor локально
cd banxe-training-data
python scripts/ingest_processor.py

# Проверить результат
cat knowledge-base/index.json
cat knowledge-base/README.md
```

### Требования к файлам

| Тип | Макс. размер | Кодировка | Примечания |
|-----|--------------|-----------|------------|
| PDF | 50 MB | N/A | Max 500 страниц |
| DOCX | 20 MB | UTF-8 | Без макросов |
| CSV | 100 MB | UTF-8 | Разделитель: запятая или точка с запятой |
| JSON | 50 MB | UTF-8 | Валидный JSON |
| PNG/JPG | 10 MB | N/A | Max 4096x4096 |

---

## 🛠️ Troubleshooting

### Проблема: Workflow не запускается

**Проверьте:**
1. Файлы действительно в `raw/` (не в корне)
2. Push был в `main` или `master` ветку
3. GitHub Actions не disabled в настройках репозитория

### Проблема: PDF не извлекается текст

**Возможные причины:**
- PDF сканированный (картинка, не текст)
- PDF защищён паролем
- pymupdf не распознал формат

**Решение:**
- Конвертировать в текст externally (Adobe Acrobat, online OCR)
- Загрузить как `.txt` напрямую

### Проблема: Большой файл (>100MB)

GitHub имеет лимит 100MB на файл.

**Решения:**
1. Разделить на части (split PDF)
2. Использовать Git LFS (Large File Storage)
3. Загрузить на S3/Google Drive, добавить ссылку в `raw/links/`

---

## 📊 Мониторинг

### Просмотр статистики

Открыть `knowledge-base/index.json`:

```json
{
  "version": "1.0",
  "updated_at": "2026-04-03T15:30:00",
  "total_files": 42,
  "categories": {
    "docs": [ ... ],
    "data": [ ... ],
    "media": [ ... ],
    "links": [ ... ]
  }
}
```

### Уведомления

GitHub отправляет email notification при каждом успешном workflow.

Настроить: Settings → Notifications → Choose notifications for...

---

## 🤝 Collaboration

### Приглашение в команду

Когда будете готовы, я приглашу вас в репозиторий:

1. Пришлите ваш GitHub username
2. Я добавлю вас как collaborator с Write доступом
3. Вы сможете push напрямую без fork

### Review process

Для критичных изменений (удаление файлов, переименование):

1. Создать Pull Request вместо прямого push
2. Дождаться review от @bereg2022
3. Merge после approval

---

## 📞 Поддержка

**Вопросы и проблемы:**
- Telegram: @p314pm
- GitHub Issues: https://github.com/CarmiBanxe/banxe-training-data/issues

**Что указать в обращении:**
- Имя файла(ов)
- Ожидаемое поведение vs фактическое
- Скриншот ошибки (если есть)

---

## 🎓 Дополнительные ресурсы

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pymupdf Documentation](https://pymupdf.readthedocs.io/)
- [python-docx Guide](https://python-docx.readthedocs.io/)

---

**Last Updated:** 2026-04-03  
**Maintained by:** Banxe AI Engineering Team

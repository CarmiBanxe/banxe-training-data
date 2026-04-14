---
description: Run the training data ingest processor locally
---

Process raw files and build knowledge base:

```bash
cd /home/mmber/banxe-training-data
python scripts/ingest_processor.py
```

Output: `processed/` and `knowledge-base/index.json`

To test with a specific file:
```bash
cp /path/to/file.pdf raw/docs/
python scripts/ingest_processor.py
cat knowledge-base/index.json | python3 -m json.tool | head -30
```

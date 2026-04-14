---
description: Run full quality gate for banxe-training-data
---

```bash
cd /home/mmber/banxe-training-data
make quality-gate
```

Runs: ruff lint → pytest tests/ → secrets scan

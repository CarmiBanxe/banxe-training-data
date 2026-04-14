.PHONY: install ingest test lint quality-gate secrets-scan clean

install:
	pip install -r requirements.txt -r requirements-dev.txt

ingest:
	python scripts/ingest_processor.py

test:
	pytest tests/ -v --tb=short

test-coverage:
	pytest tests/ -v --cov=scripts --cov-report=term-missing --cov-fail-under=80

lint:
	ruff check scripts/ tests/
	ruff format --check scripts/ tests/

quality-gate: lint test
	@echo "✅ Quality gate PASSED"

secrets-scan:
	@command -v gitleaks >/dev/null && gitleaks detect --source . --verbose || echo "[SKIP] gitleaks not installed"

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .pytest_cache .ruff_cache

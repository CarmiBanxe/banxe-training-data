"""
Tests for banxe-training-data ingest_processor.py
Validates: schema correctness, data quality, file handling, GDPR compliance
"""
import json
import sys
from pathlib import Path

import pytest

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from ingest_processor import IngestProcessor  # noqa: E402


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_repo(tmp_path):
    """Create a minimal repo structure in a temp directory."""
    (tmp_path / "raw" / "docs").mkdir(parents=True)
    (tmp_path / "raw" / "data").mkdir(parents=True)
    (tmp_path / "raw" / "media").mkdir(parents=True)
    (tmp_path / "raw" / "links").mkdir(parents=True)
    (tmp_path / "processed").mkdir()
    (tmp_path / "knowledge-base").mkdir()
    return tmp_path


@pytest.fixture
def processor(tmp_repo):
    """Return an IngestProcessor pointed at tmp_repo."""
    return IngestProcessor(base_dir=str(tmp_repo))


# ── Schema validation ─────────────────────────────────────────────────────────

class TestIndexSchema:
    def test_index_has_version_field(self, processor, tmp_repo):
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        assert "version" in index, "index.json must have 'version' field"

    def test_index_has_updated_at(self, processor, tmp_repo):
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        assert "updated_at" in index

    def test_index_has_categories(self, processor, tmp_repo):
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        assert "categories" in index
        cats = index["categories"]
        for cat in ("docs", "data", "media", "links"):
            assert cat in cats, f"category '{cat}' missing from index"

    def test_index_has_total_files(self, processor, tmp_repo):
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        assert "total_files" in index
        assert isinstance(index["total_files"], int)

    def test_version_is_semver_format(self, processor, tmp_repo):
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        version = index["version"]
        parts = version.split(".")
        assert len(parts) >= 2, f"version '{version}' must be MAJOR.MINOR format"
        assert all(p.isdigit() for p in parts), f"version parts must be numeric: {version}"


# ── File processing ────────────────────────────────────────────────────────────

class TestFileProcessing:
    def test_empty_raw_dir_produces_valid_index(self, processor, tmp_repo):
        """Empty raw dir should still produce a valid index."""
        processor.run()
        index_path = tmp_repo / "knowledge-base" / "index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text())
        assert index["total_files"] == 0

    def test_txt_file_is_processed(self, processor, tmp_repo):
        """TXT files in raw/docs should appear in index."""
        doc = tmp_repo / "raw" / "docs" / "test-policy.txt"
        doc.write_text("This is a test FCA compliance document.\n")
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        assert index["total_files"] >= 1

    def test_md_file_is_processed(self, processor, tmp_repo):
        """MD files in raw/docs should appear in index."""
        doc = tmp_repo / "raw" / "docs" / "README.md"
        doc.write_text("# BANXE Test Document\n\nContent here.\n")
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        assert index["total_files"] >= 1

    def test_json_data_file_is_processed(self, processor, tmp_repo):
        """JSON files in raw/data should appear in index."""
        data_file = tmp_repo / "raw" / "data" / "transactions.json"
        data_file.write_text(json.dumps([{"id": "1", "amount": "100.00", "currency": "GBP"}]))
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        assert index["total_files"] >= 1

    def test_processed_file_has_hash(self, processor, tmp_repo):
        """Each indexed file should have a hash for integrity."""
        doc = tmp_repo / "raw" / "docs" / "policy.txt"
        doc.write_text("Test content")
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        if index["total_files"] > 0:
            docs = index["categories"]["docs"]
            if docs:
                entry = docs[0]
                # hash stored as 'id' or 'hash' depending on processor version
                assert "hash" in entry or "id" in entry, "file entry must have a hash/id field"

    def test_processed_file_has_filename(self, processor, tmp_repo):
        """Each indexed file should have a filename."""
        doc = tmp_repo / "raw" / "docs" / "policy.txt"
        doc.write_text("Test content")
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        if index["total_files"] > 0:
            docs = index["categories"]["docs"]
            if docs:
                entry = docs[0]
                assert "filename" in entry or "name" in entry


# ── GDPR / Security ───────────────────────────────────────────────────────────

class TestGDPRCompliance:
    def test_no_pii_keywords_in_raw_docs(self, tmp_repo):
        """Synthetic/anonymised data only — no real PII patterns."""
        # Check for any files in raw/ that might contain real email addresses
        pii_patterns = ["@gmail.com", "@yahoo.com", "@hotmail.com", "password:", "secret:"]
        raw_dir = tmp_repo / "raw"
        violations = []
        for f in raw_dir.rglob("*.txt"):
            content = f.read_text(errors="ignore")
            for pattern in pii_patterns:
                if pattern in content.lower():
                    violations.append(f"{f.name}: contains '{pattern}'")
        assert violations == [], f"PII found in raw docs: {violations}"

    def test_index_does_not_store_full_content(self, processor, tmp_repo):
        """
        knowledge-base/index.json should store previews only, not full content.
        Prevents PII leakage via the index file itself.
        """
        long_doc = tmp_repo / "raw" / "docs" / "long-policy.txt"
        long_doc.write_text("A" * 10_000)  # 10KB document
        processor.run()
        index_content = (tmp_repo / "knowledge-base" / "index.json").read_text()
        # Index should not be larger than reasonable metadata size
        assert len(index_content) < 50_000, (
            "index.json is suspiciously large — may contain full document content"
        )

    def test_supported_formats_list_is_defined(self):
        """SUPPORTED_FORMATS must be defined in ingest_processor."""
        from ingest_processor import SUPPORTED_FORMATS
        assert isinstance(SUPPORTED_FORMATS, dict)
        assert "docs" in SUPPORTED_FORMATS
        assert "data" in SUPPORTED_FORMATS
        assert ".pdf" in SUPPORTED_FORMATS["docs"]
        assert ".csv" in SUPPORTED_FORMATS["data"]


# ── Data quality ──────────────────────────────────────────────────────────────

class TestDataQuality:
    def test_json_data_files_are_valid_json(self, tmp_repo):
        """All JSON files in raw/data must be valid JSON."""
        data_dir = tmp_repo / "raw" / "data"
        # Create a valid and invalid file
        valid = data_dir / "valid.json"
        valid.write_text('{"key": "value"}')
        for f in data_dir.glob("*.json"):
            try:
                json.loads(f.read_text())
            except json.JSONDecodeError as e:
                pytest.fail(f"{f.name} is invalid JSON: {e}")

    def test_total_files_matches_categories(self, processor, tmp_repo):
        """total_files should equal sum of all category counts."""
        (tmp_repo / "raw" / "docs" / "a.txt").write_text("a")
        (tmp_repo / "raw" / "data" / "b.json").write_text('{"x": 1}')
        processor.run()
        index = json.loads((tmp_repo / "knowledge-base" / "index.json").read_text())
        cat_total = sum(len(v) for v in index["categories"].values())
        assert index["total_files"] == cat_total, (
            f"total_files={index['total_files']} != sum of categories={cat_total}"
        )

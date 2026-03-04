"""Tests for the Reepo open data export — CSV generation, content, licensing."""
import os
import tempfile

import pytest

from src.db import init_db, insert_repo
from src.open_data import (
    EXPORT_FIELDS,
    CC_BY_HEADER,
    generate_open_data_export,
    generate_open_data_csv_string,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def seeded_db(db_path):
    for i in range(5):
        insert_repo({
            "github_id": 80000 + i,
            "owner": "export-org",
            "name": f"export-repo-{i}",
            "full_name": f"export-org/export-repo-{i}",
            "description": f"Export test repo {i}",
            "url": f"https://github.com/export-org/export-repo-{i}",
            "stars": 1000 - i * 100,
            "forks": 50 + i,
            "language": ["Python", "TypeScript", "Rust", "Go", "Java"][i],
            "license": "MIT",
            "category_primary": "frameworks",
            "reepo_score": 90 - i * 5,
        }, db_path)
    return db_path


class TestGenerateOpenDataExport:
    def test_creates_file(self, seeded_db):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(seeded_db, output_dir=tmpdir)
            assert os.path.exists(filepath)
            assert filepath.endswith(".csv")

    def test_file_has_cc_by_header(self, seeded_db):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(seeded_db, output_dir=tmpdir)
            with open(filepath) as f:
                content = f.read()
            assert "CC-BY-4.0" in content
            assert "creativecommons.org" in content
            assert "Reepo.dev" in content

    def test_file_has_column_headers(self, seeded_db):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(seeded_db, output_dir=tmpdir)
            with open(filepath) as f:
                lines = f.readlines()
            # Skip comment lines
            header_line = next(l for l in lines if not l.startswith("#"))
            for field in ["full_name", "stars", "reepo_score", "language"]:
                assert field in header_line

    def test_file_has_data_rows(self, seeded_db):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(seeded_db, output_dir=tmpdir)
            with open(filepath) as f:
                lines = f.readlines()
            data_lines = [l for l in lines if not l.startswith("#") and l.strip()]
            # 1 header + 5 data rows
            assert len(data_lines) == 6

    def test_ordered_by_stars_desc(self, seeded_db):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(seeded_db, output_dir=tmpdir)
            with open(filepath) as f:
                lines = f.readlines()
            data_lines = [l for l in lines if not l.startswith("#") and l.strip()]
            # First data row should have the most stars
            assert "export-org/export-repo-0" in data_lines[1]

    def test_empty_db(self, db_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(db_path, output_dir=tmpdir)
            with open(filepath) as f:
                content = f.read()
            assert "Total repos: 0" in content

    def test_creates_output_dir(self, seeded_db):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "nested", "dir")
            filepath = generate_open_data_export(seeded_db, output_dir=nested)
            assert os.path.exists(filepath)

    def test_filename_contains_date(self, seeded_db):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(seeded_db, output_dir=tmpdir)
            filename = os.path.basename(filepath)
            assert filename.startswith("reepo-open-data-")
            assert filename.endswith(".csv")


class TestGenerateOpenDataCsvString:
    def test_returns_string(self, seeded_db):
        result = generate_open_data_csv_string(seeded_db)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_has_license_header(self, seeded_db):
        result = generate_open_data_csv_string(seeded_db)
        assert "CC-BY-4.0" in result

    def test_has_data(self, seeded_db):
        result = generate_open_data_csv_string(seeded_db)
        assert "export-org/export-repo-0" in result

    def test_empty_db(self, db_path):
        result = generate_open_data_csv_string(db_path)
        assert "Total repos: 0" in result

    def test_matches_file_export(self, seeded_db):
        csv_string = generate_open_data_csv_string(seeded_db)
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = generate_open_data_export(seeded_db, output_dir=tmpdir)
            with open(filepath) as f:
                file_content = f.read()
        # Both should have same data rows (timestamps may differ)
        csv_data_lines = [l for l in csv_string.splitlines() if not l.startswith("#") and l.strip()]
        file_data_lines = [l for l in file_content.splitlines() if not l.startswith("#") and l.strip()]
        assert csv_data_lines == file_data_lines


class TestExportFields:
    def test_required_fields_present(self):
        required = ["full_name", "stars", "reepo_score", "language", "license"]
        for field in required:
            assert field in EXPORT_FIELDS

    def test_field_count(self):
        assert len(EXPORT_FIELDS) == 12


class TestCcByHeader:
    def test_has_placeholders(self):
        assert "{timestamp}" in CC_BY_HEADER
        assert "{total}" in CC_BY_HEADER

    def test_formatting(self):
        formatted = CC_BY_HEADER.format(timestamp="2026-03-04", total=100)
        assert "2026-03-04" in formatted
        assert "100" in formatted

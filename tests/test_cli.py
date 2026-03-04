"""Tests for the Reepo CLI."""
import os
import subprocess
import sys
import tempfile

import pytest


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )


# --- Help / no-args ---

class TestCliBasic:
    def test_help(self):
        result = _run_cli("--help")
        assert result.returncode == 0
        assert "Reepo.dev" in result.stdout

    def test_no_args(self):
        result = _run_cli()
        assert result.returncode == 0

    def test_help_mentions_crawl(self):
        result = _run_cli("--help")
        assert "crawl" in result.stdout

    def test_help_mentions_analyze(self):
        result = _run_cli("--help")
        assert "analyze" in result.stdout

    def test_help_mentions_stats(self):
        result = _run_cli("--help")
        assert "stats" in result.stdout

    def test_help_mentions_seed(self):
        result = _run_cli("--help")
        assert "seed" in result.stdout

    def test_help_mentions_serve(self):
        result = _run_cli("--help")
        assert "serve" in result.stdout

    def test_help_mentions_search(self):
        result = _run_cli("--help")
        assert "search" in result.stdout


# --- Crawl ---

class TestCliCrawl:
    def test_crawl_help(self):
        result = _run_cli("crawl", "--help")
        assert result.returncode == 0
        assert "--topic" in result.stdout
        assert "--db" in result.stdout
        assert "--token" in result.stdout

    def test_crawl_db_flag(self):
        result = _run_cli("crawl", "--help")
        assert "--db" in result.stdout


# --- Analyze ---

class TestCliAnalyze:
    def test_analyze_help(self):
        result = _run_cli("analyze", "--help")
        assert result.returncode == 0
        assert "--db" in result.stdout

    def test_analyze_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            result = _run_cli("analyze", "--db", db_path)
            assert result.returncode == 0
            assert "Analyzed" in result.stdout


# --- Stats ---

class TestCliStats:
    def test_stats_help(self):
        result = _run_cli("stats", "--help")
        assert result.returncode == 0
        assert "--db" in result.stdout

    def test_stats_empty_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            result = _run_cli("stats", "--db", db_path)
            assert result.returncode == 0
            assert "Total repos: 0" in result.stdout

    def test_stats_with_seed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            _run_cli("seed", "--db", db_path)
            result = _run_cli("stats", "--db", db_path)
            assert result.returncode == 0
            assert "Total repos: 50" in result.stdout
            assert "Repos by category:" in result.stdout
            assert "Top languages:" in result.stdout
            assert "Average Reepo Score:" in result.stdout


# --- Seed ---

class TestCliSeed:
    def test_seed_help(self):
        result = _run_cli("seed", "--help")
        assert result.returncode == 0
        assert "--db" in result.stdout

    def test_seed_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            result = _run_cli("seed", "--db", db_path)
            assert result.returncode == 0
            assert "Seeded 50 repos" in result.stdout

    def test_seed_creates_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            _run_cli("seed", "--db", db_path)
            assert os.path.exists(db_path)

    def test_seed_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            _run_cli("seed", "--db", db_path)
            result = _run_cli("seed", "--db", db_path)
            assert result.returncode == 0


# --- Serve ---

class TestCliServe:
    def test_serve_help(self):
        result = _run_cli("serve", "--help")
        assert result.returncode == 0
        assert "--db" in result.stdout
        assert "--port" in result.stdout


# --- Search ---

class TestCliSearch:
    def test_search_help(self):
        result = _run_cli("search", "--help")
        assert result.returncode == 0
        assert "--sort" in result.stdout
        assert "--limit" in result.stdout

    def test_search_no_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            result = _run_cli("search", "nonexistent", "--db", db_path)
            assert result.returncode == 0
            assert "No results found" in result.stdout

    def test_search_with_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            _run_cli("seed", "--db", db_path)
            result = _run_cli("search", "langchain", "--db", db_path)
            assert result.returncode == 0
            assert "langchain" in result.stdout.lower()

    def test_search_with_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            _run_cli("seed", "--db", db_path)
            result = _run_cli("search", "ai", "--db", db_path, "--limit", "3")
            assert result.returncode == 0

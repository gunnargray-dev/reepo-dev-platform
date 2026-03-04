"""Tests for the Reepo CLI."""
import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Reepo.dev" in result.stdout


def test_cli_no_args():
    result = subprocess.run(
        [sys.executable, "-m", "src.cli"],
        capture_output=True, text=True
    )
    assert result.returncode == 0


def test_cli_crawl_placeholder():
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "crawl"],
        capture_output=True, text=True
    )
    assert "not yet implemented" in result.stdout.lower() or result.returncode == 0

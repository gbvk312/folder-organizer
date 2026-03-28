"""Shared test fixtures for folder organizer tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample files of various types."""
    files = [
        "photo.jpg",
        "report.pdf",
        "song.mp3",
        "video.mp4",
        "archive.zip",
        "script.py",
        "data.csv",
        "readme.txt",
        "installer.exe",
        "run.sh",
    ]
    for name in files:
        (tmp_path / name).write_text(f"dummy content for {name}")
    return tmp_path


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a temporary config.json with custom categories."""
    config = {"TestCategory": [".xyz", ".abc"]}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    return path


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Create an empty temporary directory."""
    return tmp_path

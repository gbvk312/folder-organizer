"""Tests for the folder organizer."""

import json
from pathlib import Path

import pytest

from organize_folders import (
    DEFAULT_FILE_TYPE_MAP,
    UNDO_MANIFEST,
    build_extension_map,
    get_unique_path,
    load_config,
    main,
    organize_directory,
    parse_args,
    print_summary,
    setup_logging,
    should_skip,
    undo_organization,
)

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample files."""
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
    """Create a temporary config.json."""
    config = {"TestCategory": [".xyz", ".abc"]}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    return path


# ── Unit Tests: build_extension_map ───────────────────────────────────


class TestBuildExtensionMap:
    def test_basic_mapping(self) -> None:
        mapping = {"Images": [".jpg", ".png"], "Audio": [".mp3"]}
        result = build_extension_map(mapping)
        assert result[".jpg"] == "Images"
        assert result[".png"] == "Images"
        assert result[".mp3"] == "Audio"

    def test_case_insensitive(self) -> None:
        mapping = {"Images": [".JPG", ".PNG"]}
        result = build_extension_map(mapping)
        assert result[".jpg"] == "Images"
        assert result[".png"] == "Images"

    def test_empty_mapping(self) -> None:
        assert build_extension_map({}) == {}

    def test_duplicate_extension_last_wins(self) -> None:
        """When the same extension appears in multiple categories, the last one wins."""
        mapping = {"Code": [".py"], "Scripts": [".py"]}
        result = build_extension_map(mapping)
        assert result[".py"] == "Scripts"


# ── Unit Tests: get_unique_path ───────────────────────────────────────


class TestGetUniquePath:
    def test_no_conflict(self, tmp_path: Path) -> None:
        dest = tmp_path / "file.txt"
        assert get_unique_path(dest) == dest

    def test_single_conflict(self, tmp_path: Path) -> None:
        existing = tmp_path / "file.txt"
        existing.write_text("exists")
        result = get_unique_path(existing)
        assert result == tmp_path / "file_1.txt"

    def test_multiple_conflicts(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").write_text("v0")
        (tmp_path / "file_1.txt").write_text("v1")
        result = get_unique_path(tmp_path / "file.txt")
        assert result == tmp_path / "file_2.txt"


# ── Unit Tests: should_skip ───────────────────────────────────────────


class TestShouldSkip:
    def test_skip_hidden_files(self, tmp_path: Path) -> None:
        assert should_skip(tmp_path / ".hidden", tmp_path) is True

    def test_skip_ds_store(self, tmp_path: Path) -> None:
        assert should_skip(tmp_path / ".DS_Store", tmp_path) is True

    def test_normal_file(self, tmp_path: Path) -> None:
        assert should_skip(tmp_path / "report.pdf", tmp_path) is False

    def test_skip_symlinks(self, tmp_path: Path) -> None:
        """Symlinks should be skipped to prevent escaping target directory."""
        real_file = tmp_path / "real.txt"
        real_file.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(real_file)
        assert should_skip(link, tmp_path) is True

    def test_skip_undo_manifest(self, tmp_path: Path) -> None:
        """The undo manifest file should always be skipped."""
        assert should_skip(tmp_path / UNDO_MANIFEST, tmp_path) is True


# ── Unit Tests: load_config ──────────────────────────────────────────


class TestLoadConfig:
    def test_load_custom_config(self, config_file: Path) -> None:
        result = load_config(config_file)
        assert "TestCategory" in result
        assert ".xyz" in result["TestCategory"]

    def test_load_missing_config(self, tmp_path: Path) -> None:
        result = load_config(tmp_path / "nonexistent.json")
        assert result == DEFAULT_FILE_TYPE_MAP

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{invalid json")
        result = load_config(bad)
        assert result == DEFAULT_FILE_TYPE_MAP


# ── Unit Tests: parse_args ───────────────────────────────────────────


class TestParseArgs:
    def test_defaults(self) -> None:
        args = parse_args([])
        assert args.directory == "."
        assert args.dry_run is False
        assert args.undo is False
        assert args.verbose is False

    def test_custom_dir(self) -> None:
        args = parse_args(["/some/path"])
        assert args.directory == "/some/path"

    def test_dry_run(self) -> None:
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_undo_flag(self) -> None:
        args = parse_args(["--undo"])
        assert args.undo is True

    def test_verbose_flag(self) -> None:
        args = parse_args(["--verbose"])
        assert args.verbose is True

    def test_all_options(self) -> None:
        args = parse_args(
            ["/dir", "--dry-run", "--config", "c.json", "--log-file", "log.txt", "--verbose"]
        )
        assert args.directory == "/dir"
        assert args.dry_run is True
        assert args.config == "c.json"
        assert args.log_file == "log.txt"
        assert args.verbose is True


# ── Unit Tests: setup_logging ────────────────────────────────────────


class TestSetupLogging:
    def test_default_logging(self) -> None:
        logger = setup_logging()
        assert len(logger.handlers) == 1  # console only

    def test_logging_with_file(self, tmp_path: Path) -> None:
        log_path = tmp_path / "test.log"
        logger = setup_logging(log_file=log_path)
        assert len(logger.handlers) == 2  # console + file
        logger.info("test message")
        assert log_path.exists()
        assert "test message" in log_path.read_text()

    def test_verbose_logging(self) -> None:
        logger = setup_logging(verbose=True)
        console_handler = logger.handlers[0]
        assert console_handler.level == 10  # DEBUG level

    def test_no_handler_duplication(self) -> None:
        """Calling setup_logging multiple times should not add duplicate handlers."""
        setup_logging()
        logger = setup_logging()
        assert len(logger.handlers) == 1


# ── Unit Tests: print_summary ────────────────────────────────────────


class TestPrintSummary:
    def test_summary_output(self, capsys) -> None:
        counts = {"Images": 3, "Documents": 2}
        print_summary(counts)
        captured = capsys.readouterr()
        assert "Images" in captured.out
        assert "Documents" in captured.out
        assert "5 file(s)" in captured.out

    def test_summary_dry_run_label(self, capsys) -> None:
        counts = {"Images": 1}
        print_summary(counts, dry_run=True)
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out


# ── Integration Tests: organize_directory ─────────────────────────────


class TestOrganizeDirectory:
    def test_files_moved_to_categories(self, sample_dir: Path) -> None:
        counts = organize_directory(sample_dir, DEFAULT_FILE_TYPE_MAP)
        assert (sample_dir / "Images" / "photo.jpg").exists()
        assert (sample_dir / "Documents" / "report.pdf").exists()
        assert (sample_dir / "Audio" / "song.mp3").exists()
        assert (sample_dir / "Videos" / "video.mp4").exists()
        assert (sample_dir / "Archives" / "archive.zip").exists()
        assert (sample_dir / "Code" / "script.py").exists()
        assert (sample_dir / "Data" / "data.csv").exists()
        assert (sample_dir / "Documents" / "readme.txt").exists()
        assert (sample_dir / "Executables" / "installer.exe").exists()
        assert (sample_dir / "Scripts" / "run.sh").exists()
        assert sum(counts.values()) == 10

    def test_dry_run_no_changes(self, sample_dir: Path) -> None:
        counts = organize_directory(sample_dir, DEFAULT_FILE_TYPE_MAP, dry_run=True)
        # Files should still be in root
        assert (sample_dir / "photo.jpg").exists()
        assert not (sample_dir / "Images").exists()
        assert sum(counts.values()) == 10

    def test_conflict_resolution(self, sample_dir: Path) -> None:
        # Create a conflict: Images/photo.jpg already exists
        (sample_dir / "Images").mkdir()
        (sample_dir / "Images" / "photo.jpg").write_text("original")

        organize_directory(sample_dir, DEFAULT_FILE_TYPE_MAP)
        assert (sample_dir / "Images" / "photo.jpg").exists()
        assert (sample_dir / "Images" / "photo_1.jpg").exists()

    def test_unknown_extension(self, tmp_path: Path) -> None:
        (tmp_path / "weird.qwerty").write_text("content")
        counts = organize_directory(tmp_path, DEFAULT_FILE_TYPE_MAP)
        assert (tmp_path / "Other" / "weird.qwerty").exists()
        assert counts.get("Other") == 1

    def test_file_no_extension(self, tmp_path: Path) -> None:
        """Files with no extension should be categorized as 'Other'."""
        (tmp_path / "Makefile").write_text("all: build")
        counts = organize_directory(tmp_path, DEFAULT_FILE_TYPE_MAP)
        assert (tmp_path / "Other" / "Makefile").exists()
        assert counts.get("Other") == 1

    def test_empty_directory(self, tmp_path: Path) -> None:
        counts = organize_directory(tmp_path, DEFAULT_FILE_TYPE_MAP)
        assert counts == {}

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        counts = organize_directory(tmp_path / "nope", DEFAULT_FILE_TYPE_MAP)
        assert counts == {}

    def test_symlinks_not_moved(self, tmp_path: Path) -> None:
        """Symlinked files should be skipped entirely."""
        real_file = tmp_path / "real.txt"
        real_file.write_text("real content")
        link = tmp_path / "link.txt"
        link.symlink_to(real_file)

        counts = organize_directory(tmp_path, DEFAULT_FILE_TYPE_MAP)
        # real.txt moved, link.txt skipped
        assert (tmp_path / "Documents" / "real.txt").exists()
        assert link.is_symlink()  # symlink untouched
        assert counts.get("Documents") == 1

    def test_undo_manifest_created(self, sample_dir: Path) -> None:
        """An undo manifest should be written after organizing."""
        organize_directory(sample_dir, DEFAULT_FILE_TYPE_MAP)
        manifest_path = sample_dir / UNDO_MANIFEST
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert len(manifest) == 10

    def test_dry_run_no_manifest(self, sample_dir: Path) -> None:
        """Dry run should NOT create an undo manifest."""
        organize_directory(sample_dir, DEFAULT_FILE_TYPE_MAP, dry_run=True)
        assert not (sample_dir / UNDO_MANIFEST).exists()

    def test_unicode_filenames(self, tmp_path: Path) -> None:
        """Files with unicode names should be handled correctly."""
        (tmp_path / "日本語.txt").write_text("japanese")
        (tmp_path / "café.pdf").write_text("french")
        counts = organize_directory(tmp_path, DEFAULT_FILE_TYPE_MAP)
        assert (tmp_path / "Documents" / "日本語.txt").exists()
        assert (tmp_path / "Documents" / "café.pdf").exists()
        assert counts.get("Documents") == 2


# ── Integration Tests: undo_organization ──────────────────────────────


class TestUndoOrganization:
    def test_undo_reverses_moves(self, sample_dir: Path) -> None:
        """Undo should restore files to their original locations."""
        organize_directory(sample_dir, DEFAULT_FILE_TYPE_MAP)
        assert not (sample_dir / "photo.jpg").exists()

        success = undo_organization(sample_dir)
        assert success is True
        assert (sample_dir / "photo.jpg").exists()
        assert (sample_dir / "report.pdf").exists()
        assert not (sample_dir / UNDO_MANIFEST).exists()

    def test_undo_cleans_empty_dirs(self, sample_dir: Path) -> None:
        """Undo should remove empty category directories."""
        organize_directory(sample_dir, DEFAULT_FILE_TYPE_MAP)
        assert (sample_dir / "Images").exists()

        undo_organization(sample_dir)
        assert not (sample_dir / "Images").exists()

    def test_undo_no_manifest(self, tmp_path: Path) -> None:
        """Undo without a manifest should return False."""
        success = undo_organization(tmp_path)
        assert success is False

    def test_undo_corrupt_manifest(self, tmp_path: Path) -> None:
        """Undo with a corrupt manifest should return False."""
        (tmp_path / UNDO_MANIFEST).write_text("{bad json")
        success = undo_organization(tmp_path)
        assert success is False


# ── End-to-End Tests: main ────────────────────────────────────────────


class TestMain:
    def test_main_success(self, sample_dir: Path) -> None:
        result = main([str(sample_dir)])
        assert result == 0

    def test_main_dry_run(self, sample_dir: Path) -> None:
        result = main([str(sample_dir), "--dry-run"])
        assert result == 0
        # Files should not have been moved
        assert (sample_dir / "photo.jpg").exists()

    def test_main_verbose(self, sample_dir: Path) -> None:
        result = main([str(sample_dir), "--verbose"])
        assert result == 0

    def test_main_undo(self, sample_dir: Path) -> None:
        main([str(sample_dir)])
        result = main([str(sample_dir), "--undo"])
        assert result == 0
        assert (sample_dir / "photo.jpg").exists()

    def test_main_undo_no_manifest(self, tmp_path: Path) -> None:
        result = main([str(tmp_path), "--undo"])
        assert result == 1

    def test_main_empty_directory(self, tmp_path: Path) -> None:
        result = main([str(tmp_path)])
        assert result == 0

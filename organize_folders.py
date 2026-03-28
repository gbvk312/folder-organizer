#!/usr/bin/env python3
"""Folder Organizer - Organize files into categorized subfolders."""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

from colorama import Fore, Style, init

init(autoreset=True)

# Default file type mappings (used when config.json is not found)
DEFAULT_FILE_TYPE_MAP: dict[str, list[str]] = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"],
    "Documents": [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    ],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Code": [
        ".py",
        ".js",
        ".html",
        ".css",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".rb",
        ".php",
        ".go",
        ".rs",
        ".swift",
        ".kt",
        ".kts",
        ".ts",
        ".tsx",
    ],
    "Executables": [".exe", ".dmg", ".app", ".deb", ".rpm", ".msi"],
    "Scripts": [".sh", ".bat", ".ps1", ".cmd"],
    "Data": [".json", ".xml", ".csv", ".sql", ".db", ".sqlite"],
}

SKIP_FILES = {".DS_Store", "Thumbs.db", ".gitignore", ".gitkeep"}
SCRIPT_NAME = Path(__file__).name
UNDO_MANIFEST = ".organizer_undo.json"


def setup_logging(
    log_file: Optional[Path] = None,
    verbose: bool = False,
) -> logging.Logger:
    """Configure logging to console and optional file.

    Args:
        log_file: Optional path for persistent log output.
        verbose: If True, set console output to DEBUG level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("folder_organizer")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers on repeated calls (e.g. during tests)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


def load_config(config_path: Path) -> dict[str, list[str]]:
    """Load file type mappings from a JSON config file.

    Args:
        config_path: Path to the JSON configuration file.

    Returns:
        Dictionary mapping category names to lists of extensions.
    """
    if config_path.is_file():
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(
                f"{Fore.YELLOW}Warning: Could not load config ({e}). "
                f"Using defaults.{Style.RESET_ALL}"
            )
    return DEFAULT_FILE_TYPE_MAP


def build_extension_map(file_type_map: dict[str, list[str]]) -> dict[str, str]:
    """Build a reverse map from extension to category name.

    Args:
        file_type_map: Category-to-extensions mapping.

    Returns:
        Dictionary mapping each extension to its category.
    """
    ext_map: dict[str, str] = {}
    for category, extensions in file_type_map.items():
        for ext in extensions:
            ext_map[ext.lower()] = category
    return ext_map


def get_unique_path(dest: Path) -> Path:
    """Return a unique file path by appending a numeric suffix if needed.

    Args:
        dest: The desired destination path.

    Returns:
        A path that does not conflict with existing files.
    """
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def should_skip(file_path: Path, target_dir: Path) -> bool:
    """Determine if a file should be skipped during organization.

    Skips: the organizer script itself, known system files, hidden files,
    symlinks, and the undo manifest.

    Args:
        file_path: The file to check.
        target_dir: The directory being organized.

    Returns:
        True if the file should be skipped.
    """
    name = file_path.name
    if name == SCRIPT_NAME:
        return True
    if name in SKIP_FILES:
        return True
    if name.startswith("."):
        return True
    if name == UNDO_MANIFEST:
        return True
    return bool(file_path.is_symlink())


def organize_directory(
    target_dir: Path,
    file_type_map: dict[str, list[str]],
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> dict[str, int]:
    """Organize files in a directory into categorized subfolders.

    Args:
        target_dir: Directory to organize.
        file_type_map: Category-to-extensions mapping.
        dry_run: If True, only preview changes without moving files.
        logger: Optional logger instance.

    Returns:
        Dictionary with counts of files moved per category.
    """
    if logger is None:
        logger = logging.getLogger("folder_organizer")

    ext_map = build_extension_map(file_type_map)
    counts: dict[str, int] = {}
    manifest: dict[str, str] = {}

    if not target_dir.is_dir():
        logger.error(f"Directory not found: {target_dir}")
        return counts

    try:
        files = [f for f in target_dir.iterdir() if f.is_file() and not should_skip(f, target_dir)]
    except PermissionError:
        logger.error(f"Permission denied: {target_dir}")
        return counts

    if not files:
        logger.info(f"{Fore.YELLOW}No files to organize in {target_dir}")
        return counts

    logger.info(f"{Fore.CYAN}Found {len(files)} file(s) to organize.")

    for file_path in sorted(files):
        ext = file_path.suffix.lower()
        category = ext_map.get(ext, "Other")
        category_dir = target_dir / category

        if dry_run:
            logger.info(f"  {Fore.BLUE}[DRY RUN]{Style.RESET_ALL} {file_path.name} -> {category}/")
        else:
            try:
                category_dir.mkdir(exist_ok=True)
                dest = get_unique_path(category_dir / file_path.name)
                shutil.move(str(file_path), str(dest))
                logger.info(
                    f"  {Fore.GREEN}✓{Style.RESET_ALL} {file_path.name} -> {category}/{dest.name}"
                )
                logger.debug(f"  Moved: {file_path} -> {dest}")
                # Record for undo manifest
                manifest[str(dest)] = str(file_path)
            except PermissionError:
                logger.error(f"  {Fore.RED}✗{Style.RESET_ALL} Permission denied: {file_path.name}")
            except OSError as e:
                logger.error(f"  {Fore.RED}✗{Style.RESET_ALL} Error moving {file_path.name}: {e}")

        counts[category] = counts.get(category, 0) + 1

    # Write undo manifest (only on actual moves)
    if manifest and not dry_run:
        _write_undo_manifest(target_dir, manifest, logger)

    return counts


def _write_undo_manifest(
    target_dir: Path,
    manifest: dict[str, str],
    logger: logging.Logger,
) -> None:
    """Write the undo manifest to the target directory.

    Args:
        target_dir: Directory where the manifest is saved.
        manifest: Mapping of destination paths to original paths.
        logger: Logger instance.
    """
    manifest_path = target_dir / UNDO_MANIFEST
    try:
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.debug(f"Undo manifest saved to {manifest_path}")
    except OSError as e:
        logger.warning(f"Could not save undo manifest: {e}")


def undo_organization(
    target_dir: Path,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """Reverse a previous organization by reading the undo manifest.

    Args:
        target_dir: Directory that was previously organized.
        logger: Optional logger instance.

    Returns:
        True if undo was successful, False otherwise.
    """
    if logger is None:
        logger = logging.getLogger("folder_organizer")

    manifest_path = target_dir / UNDO_MANIFEST

    if not manifest_path.is_file():
        logger.error(
            f"{Fore.RED}No undo manifest found at {manifest_path}. Cannot undo.{Style.RESET_ALL}"
        )
        return False

    try:
        with open(manifest_path) as f:
            manifest: dict[str, str] = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"{Fore.RED}Could not read undo manifest: {e}{Style.RESET_ALL}")
        return False

    if not manifest:
        logger.info(f"{Fore.YELLOW}Undo manifest is empty. Nothing to undo.{Style.RESET_ALL}")
        return True

    errors = 0
    for dest_str, src_str in manifest.items():
        dest = Path(dest_str)
        src = Path(src_str)
        if dest.exists():
            try:
                shutil.move(str(dest), str(src))
                logger.info(
                    f"  {Fore.GREEN}↩{Style.RESET_ALL} {dest.name} -> {src.parent.name}/{src.name}"
                )
            except OSError as e:
                logger.error(f"  {Fore.RED}✗{Style.RESET_ALL} Error restoring {dest.name}: {e}")
                errors += 1
        else:
            logger.warning(
                f"  {Fore.YELLOW}⚠{Style.RESET_ALL} File not found (already moved?): {dest}"
            )
            errors += 1

    # Clean up empty category directories
    for dest_str in manifest:
        category_dir = Path(dest_str).parent
        if category_dir.is_dir() and not any(category_dir.iterdir()):
            category_dir.rmdir()
            logger.debug(f"Removed empty directory: {category_dir}")

    # Remove manifest after successful undo
    if errors == 0:
        manifest_path.unlink()
        logger.info(f"{Fore.GREEN}Undo complete. Manifest removed.{Style.RESET_ALL}")
    else:
        logger.warning(
            f"{Fore.YELLOW}Undo completed with {errors} error(s). "
            f"Manifest preserved for retry.{Style.RESET_ALL}"
        )

    return errors == 0


def print_summary(counts: dict[str, int], dry_run: bool = False) -> None:
    """Print a summary of the organization results."""
    total = sum(counts.values())
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{Fore.CYAN}{'=' * 40}")
    print(f"  {mode}Organization Summary")
    print(f"{'=' * 40}{Style.RESET_ALL}")
    for category, count in sorted(counts.items()):
        print(f"  {Fore.GREEN}{category:<15}{Style.RESET_ALL} {count} file(s)")
    print(f"{Fore.CYAN}{'=' * 40}")
    print(f"  Total: {total} file(s)")
    print(f"{'=' * 40}{Style.RESET_ALL}\n")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Organize files in a directory into categorized subfolders."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to organize (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving files",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Reverse a previous organization using the undo manifest",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom config.json",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file for recording operations",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG-level) console output",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the folder organizer.

    Returns:
        0 on success, 1 on error.
    """
    args = parse_args(argv)
    target_dir = Path(args.directory).resolve()

    logger = setup_logging(
        log_file=Path(args.log_file) if args.log_file else None,
        verbose=args.verbose,
    )

    # Handle undo mode
    if args.undo:
        logger.info(f"Undoing organization in: {target_dir}")
        success = undo_organization(target_dir, logger)
        return 0 if success else 1

    config_path = Path(args.config) if args.config else (Path(__file__).parent / "config.json")
    file_type_map = load_config(config_path)

    if args.dry_run:
        print(f"\n{Fore.YELLOW}🔍 DRY RUN MODE — no files will be moved.{Style.RESET_ALL}\n")

    logger.info(f"Organizing: {target_dir}")
    counts = organize_directory(target_dir, file_type_map, args.dry_run, logger)

    if counts:
        print_summary(counts, args.dry_run)
    else:
        print(f"\n{Fore.YELLOW}No files were organized.{Style.RESET_ALL}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Folder Organizer

A Python CLI tool that automatically organizes files in a directory by moving them into categorized subfolders based on their file type.

## Features

- **Automatic Folder Creation**: Creates folders for each file type if they don't exist.
- **File Organization**: Moves files into appropriate type-based folders.
- **Dry Run Mode**: Preview changes with `--dry-run` before moving anything.
- **Undo Support**: Reverse a previous organization with `--undo`.
- **Conflict Resolution**: Automatically appends numeric suffixes to avoid overwriting files.
- **External Configuration**: Customize file type mappings via `config.json`.
- **Logging**: Optional file logging for auditing operations.
- **Verbose Mode**: Enable debug-level output with `--verbose`.
- **Safe Operation**: Skips hidden files, system files, symlinks, and the script itself.
- **Colorized Output**: Clear, color-coded terminal output.

## Prerequisites

- Python 3.9+

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/gbvk/folder-organizer.git
   cd folder-organizer
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python organize_folders.py [directory_path] [options]
```

### Options

| Flag | Description |
|---|---|
| `directory_path` | Directory to organize (default: current directory) |
| `--dry-run` | Preview changes without moving files |
| `--undo` | Reverse a previous organization using the undo manifest |
| `--config PATH` | Path to a custom `config.json` |
| `--log-file PATH` | Save operation log to a file |
| `--verbose` | Enable debug-level console output |

### Examples

```bash
# Organize the Downloads folder
python organize_folders.py ~/Downloads

# Preview what would happen (no files moved)
python organize_folders.py ~/Downloads --dry-run

# Undo the last organization
python organize_folders.py ~/Downloads --undo

# Use a custom config, log to file, and enable verbose output
python organize_folders.py ~/Desktop --config my_config.json --log-file organizer.log --verbose
```

## File Type Categories

The script categorizes files into the following types:

| Category | Extensions |
|---|---|
| **Images** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.svg` |
| **Documents** | `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, `.xls`, `.xlsx`, `.ppt`, `.pptx` |
| **Archives** | `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2` |
| **Videos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv` |
| **Audio** | `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, `.m4a` |
| **Code** | `.py`, `.js`, `.html`, `.css`, `.java`, `.c`, `.cpp`, `.h`, `.hpp`, `.rb`, `.php`, `.go`, `.rs`, `.swift`, `.kt`, `.kts`, `.ts`, `.tsx` |
| **Executables** | `.exe`, `.dmg`, `.app`, `.deb`, `.rpm`, `.msi` |
| **Scripts** | `.sh`, `.bat`, `.ps1`, `.cmd` |
| **Data** | `.json`, `.xml`, `.csv`, `.sql`, `.db`, `.sqlite` |
| **Other** | Files with no extension or unclassified extensions |

> **Note:** Symlinked files are always skipped to prevent accidentally moving files outside the target directory.

## Configuration

Customize file type mappings by editing `config.json` in the project root:

```json
{
  "Images": [".jpg", ".jpeg", ".png"],
  "MyCustomCategory": [".xyz", ".abc"]
}
```

If a custom config cannot be loaded, the tool gracefully falls back to built-in defaults.

## Undo

After organizing, the tool saves a `.organizer_undo.json` manifest in the target directory. To reverse the operation:

```bash
python organize_folders.py ~/Downloads --undo
```

This restores all moved files to their original locations and removes empty category folders.

## Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Lint
ruff check .

# Check formatting
ruff format --check .
```

## License

MIT
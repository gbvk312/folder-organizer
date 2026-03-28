# Workflow: Test and Verify

// turbo-all

1. **Lint**
   - Run `source .venv/bin/activate && ruff check .`

2. **Format Check**
   - Run `source .venv/bin/activate && ruff format --check .`

3. **Unit & Integration Testing**
   - Run `source .venv/bin/activate && python -m pytest tests/ -v`

4. **Manual Verification**
   - Create a test directory with dummy files.
   - Run `python organize_folders.py test_dir --dry-run` to preview changes.
   - Run `python organize_folders.py test_dir` to execute.
   - Run `python organize_folders.py test_dir --undo` to verify undo.
   - Verify files are correctly moved and restored.

# TypeRead

**Read what matters. Type what you read. Improve while learning.**

TypeRead is an offline-first desktop application that turns reading material (books, PDFs, EPUBs, study notes) into an interactive typing and skill-building experience.

---

## Features
- **Deterministic Document Ingestion**: Ingests PDF, EPUB, DOCX, Markdown, and TXT with automatic header/footer cleanup, de-hyphenation, and heading structure detection.
- **Sub-50ms Keystroke Evaluation**: High-performance hot-path typing canvas with zero disk I/O on keypresses.
- **Synchronized Dual View**: Upper reading passage with active-sentence highlighting synchronized with lower typing canvas.
- **Zero AI / Offline First**: All metrics, heading classifiers, weak-key drills, and search operate locally without cloud APIs or LLMs.
- **Analytics & Retention**: Live Gross/Net WPM, accuracy, consistency standard deviation, error burst detection, and top weak-key tracking.
- **Full Text Search (FTS5)**: Instant SQLite FTS5 passage search with highlight snippets.
- **Crash Recovery & Snapshots**: Automated debounced progress and session recovery.
- **Theming**: 6 reading-focused themes (Dark, Light, Sepia, Paper, High Contrast, Midnight).

---

## Quick Start

### Windows (1-Click Run)
Double-click `run.bat` to automatically install dependencies and launch TypeRead.

### Windows (Build Standalone .exe)
Double-click `build_exe.bat` to compile `dist\TypeRead\TypeRead.exe` locally using PyInstaller.

### Linux / macOS
```bash
pip install -r requirements.txt
python app_launcher.py
```

### Running Tests
```bash
pytest -v
```

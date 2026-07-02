# SPSValidator

Standalone validator for SPS packages (`.zip`), with web interface, desktop window mode, local history in SQLite, multilingual UI, and CSV export.

## Table of Contents

1. [Overview](#overview)
2. [Main Features](#main-features)
3. [Architecture](#architecture)
4. [Requirements](#requirements)
5. [Quick Start (Development)](#quick-start-development)
6. [Usage Examples](#usage-examples)
7. [Build and Packaging (macOS, Linux, Windows)](#build-and-packaging-macos-linux-windows)
8. [Tests](#tests)
9. [Output and Local Data](#output-and-local-data)
10. [Troubleshooting](#troubleshooting)
11. [Roadmap and Contribution](#roadmap-and-contribution)
12. [License](#license)

## Overview

SPSValidator validates SPS XML packages distributed as `.zip` files.
The application can run in:

- Browser mode (Flask server only)
- Desktop mode (Pywebview window + local web server)

Validation results are persisted locally and can be reopened later in the UI.

## Main Features

- SPS `.zip` validation using packtools rules.
- Validation status by package:
  - `valid`: no issues and no exceptions
  - `invalid`: at least one validation issue
  - `error`: no issues, but there are validation exceptions
- XML article snapshot extraction:
  - XML path
  - title
  - authors
  - DOI
  - PID (publisher-id / other)
  - issue count per article
  - article status (`ok` / `issue`)
- Validation history persisted in SQLite.
- CSV export of validation issues:
  - Browser download endpoint
  - Desktop API that saves to `Downloads` and reveals the file manager location
- Multilingual interface:
  - Portuguese (`pt`, default)
  - English (`en`)
  - Spanish (`es`)
- Language persistence via cookie.
- Build metadata footer (development/runtime or macOS build version label).
- Cross-platform packaging scripts (macOS, Linux, Windows).

## Architecture

- Backend/UI: Flask
- Desktop shell: pywebview
- Validation engine: packtools
- XML parsing: lxml
- Persistence: SQLite
- Packaging: PyInstaller

Relevant modules:

- `src/spsvalidator/main.py` (entrypoint, CLI args, desktop/browser)
- `src/spsvalidator/app.py` (Flask app factory, DB bootstrap)
- `src/spsvalidator/web/routes.py` (web routes, validation, CSV download)
- `src/spsvalidator/services/validation_service.py`
- `src/spsvalidator/domain/validation.py`
- `src/spsvalidator/db/repository.py`
- `src/spsvalidator/desktop_api.py`

## Requirements

- Python 3.11+
- pip
- Virtual environment tool (`venv`)

Runtime dependencies are defined in `pyproject.toml`, including:

- Flask
- lxml
- pywebview
- packtools
- requests
- tenacity
- langdetect
- setuptools (`>=68,<82`)

## Quick Start (Development)

From the project directory:

1. Create and activate a virtual environment

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install in editable mode with dev dependencies

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```

3. Run

   ```bash
   spsvalidator
   ```

## Usage Examples

### Default desktop mode (Pywebview)

```bash
spsvalidator
```

Behavior:

- Starts local server on host `127.0.0.1` and a free ephemeral port
- Opens desktop window
- Enables native CSV save to `Downloads` through desktop API

### Browser mode (without desktop window)

```bash
spsvalidator --browser
```

Default URL:

- `http://127.0.0.1:5000`

Custom host/port:

```bash
spsvalidator --browser --host 0.0.0.0 --port 8000
```

### Select language in UI

Use route pattern:

- `/language/pt`
- `/language/en`
- `/language/es`

Example:

- `http://127.0.0.1:5000/language/en`

### CSV report download (web endpoint)

After validating a package and obtaining `history_id`:

- `GET /validation/<history_id>/report.csv`

Example:

- `http://127.0.0.1:5000/validation/2f7d.../report.csv`

### Typical user flow

1. Open app.
2. Upload SPS `.zip` package.
3. Review validation status, issues, exceptions, article snapshots.
4. Download CSV report.
5. Reopen previous validations from history.

## Build and Packaging (macOS, Linux, Windows)

All scripts are in `packaging/`.

Important:

- Run commands from the project root (where `pyproject.toml` exists)
- Activate your virtual environment first
- Scripts install dependencies and execute PyInstaller

### macOS (`.app` bundle)

Command:

```bash
bash packaging/build_macos.sh
```

What it does:

- Installs dependencies in editable mode
- Installs pyinstaller
- Generates `icon.icns`
- Generates build info metadata
- Builds app bundle

Output:

- `dist/spsvalidator.app`

Run bundled app directly via terminal (for diagnostics):

- `dist/spsvalidator.app/Contents/MacOS/spsvalidator`

### Linux (binary for AppImage pipeline)

Command:

```bash
bash packaging/build_linux.sh
```

Output:

- `dist/spsvalidator`

Note:

- Script prints guidance to convert the dist binary to AppImage using `linuxdeploy/appimagetool`

### Windows (`.exe`)

PowerShell command:

```powershell
powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1
```

Output:

- `dist/spsvalidator.exe`

## Tests

Run all tests:

```bash
pytest
```

Current tests cover:

- Validation service behavior and status computation
- Web routes (upload, validation, CSV download, language switch)
- Desktop CSV save API
- CSV export format
- Metadata extraction
- i18n normalization and translations
- Version consistency with `pyproject.toml`
- Integration execution with packtools on fixture package

## Output and Local Data

Local data directory:

- `~/.spsvalidator/`

Database:

- `~/.spsvalidator/spsvalidator.sqlite3`

Main persisted entities:

- `package_validation_history`
- `package_article_snapshot`

Desktop CSV save location:

- `~/Downloads/<package>.validation.csv`

## Troubleshooting

Issue: desktop app does not open on macOS

- Rebuild the app after updates
- Run bundled binary from terminal:
  - `dist/spsvalidator.app/Contents/MacOS/spsvalidator`
- During development, prefer browser mode:
  - `spsvalidator --browser`

Issue: `No module named 'pkg_resources'`

- Reinstall project dependencies:
  - `python -m pip install -e ".[dev]"`
- Rebuild package for your OS

Issue: `No module named 'requests'` (or similar transitive dependency)

- Reinstall project dependencies:
  - `python -m pip install -e ".[dev]"`
- Rebuild package for your OS

Issue: upload rejected

- Only SPS `.zip` packages are supported

## Roadmap and Contribution

Possible roadmap items:

- Automated AppImage generation pipeline
- Signed/notarized binaries for release channels
- More fixtures and edge-case validations
- Optional CLI report generation mode

Contribution flow:

1. Open an issue describing bug/feature.
2. Create branch and implement with tests.
3. Run `pytest` locally.
4. Open PR with clear manual test steps.

## License

This project is distributed under GPL-3.0 (see `LICENSE` at repository root).

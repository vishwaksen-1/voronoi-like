# Voronoi Warper — Cross-platform GUI

This project provides a small interactive application that generates Voronoi
cells and lets you warp their vertices with a 2D noise field. The GUI is
implemented using PyQt (supports PyQt6 and PyQt5) and Matplotlib's QtAgg
backend, so it runs as a native desktop app on Linux, macOS and Windows.

# Quick status
- `voronoi_qt.py` — the standalone GUI app (uses PyQt6 if available, falls back to PyQt5).
- `voronoi.ipynb` — the original notebook (ipywidgets cell was removed to avoid frontend issues).
- `run_voronoi.py` — small launcher that checks the environment and runs the GUI.
- `requirements.txt` — recommended dependencies to install in a virtual environment.

# Supported platforms
- Linux (X11/Wayland with a working Qt + GUI environment)
- macOS (Qt via pip works with Homebrew or system Python; use python.org installers or Homebrew Python)
- Windows 10/11 (pip installs binaries for PyQt5/6)

# Minimum tested Python
- Python 3.10+ (this repo was tested with Python 3.13 inside a virtualenv).

# Recommended installation (Linux/macOS/Windows)
1. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (powershell)
# .\.venv\Scripts\Activate.ps1
# Windows (cmd)
# .\.venv\Scripts\activate.bat
```

2. Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Run the app:

```bash
python run_voronoi.py
# or directly
python voronoi_qt.py
```

# Notes and platform-specific tips
- Linux
  - Make sure you run the GUI on a machine with a display (DISPLAY or Wayland). If you're using WSL, consider using an X server or adopting a browser-based notebook workflow.
  - If using a remote machine, run with X forwarding or use the notebook alternative.

- macOS
  - If pip-installed PyQt6 bundles fail to start, try installing the Qt runtime via Homebrew: `brew install pyqt` or use PyQt5 instead.

- Windows
  - Pip installs wheels for PyQt5/6; no additional steps usually required.
  - If you get backend errors from Matplotlib, ensure the default backend is a Qt backend (QtAgg). The launcher will try to set this.

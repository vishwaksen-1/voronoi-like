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
 - `stimMaker.py` — small helper to convert saved Voronoi image pairs into
   square, bordered stimuli suitable for experiments (see below).

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

## Generating experiment stimuli with stimMaker.py

The repository includes a small post-processing helper `stimMaker.py` that
turns your saved Voronoi image pairs into counterbalanced, neutral-looking
stimuli suitable for experiments (it crops to a square, applies a coloured
border and an outer white padding, and organizes results into per-pair
folders).

Usage steps

1. Create and name matching Voronoi image pairs you want to convert. For
  example: `Voronoi_original_pair1.jpg` and `Voronoi_warped_pair1.jpg`, then
  `Voronoi_original_pair2.jpg` / `Voronoi_warped_pair2.jpg`, and so on.

   IMPORTANT: The GUI saves files using a timestamped name (for example
   `Voronoi_original_01_01_23_12_00_00.svg` or similar). Before running
   `stimMaker.py` you should rename each GUI output to the pattern the
   script expects (``Voronoi_original_pairN.jpg`` and
   ``Voronoi_warped_pairN.jpg``). The script processes JPG files, so if
   your GUI output is SVG or PNG convert or export them to JPG first.
2. Place all pairs in a single directory. In the example project we used a
  folder called `dasFoto/`. Update the `INPUT_DIR` variable at the top of
  `stimMaker.py` if you use a different folder.
3. Run the script (no command-line arguments required):

```bash
python stimMaker.py
```

4. To tune appearance:
  - Change `COLOR_BORDER_WIDTH` in `stimMaker.py` to adjust the coloured
    border thickness (pixels).
  - Change `MM_WHITE_BORDER` to modify the white padding around the coloured
    square (value is in millimetres; DPI is configured by `DPI`).

Output

The script writes a `pair_<n>` folder for each pair it processes and saves a
clean cropped image plus two bordered variants (one per colour defined in
`BORDER_COLORS`).

This tool is intentionally small — if you'd like I can add command-line
arguments to control `INPUT_DIR`, border size, output format, or to run
only a single pair.
#!/usr/bin/env python3
"""Launcher for Voronoi GUI with cross-platform checks.

This script tries to choose a working Qt binding (PyQt6 preferred, then
PyQt5), ensures Matplotlib uses a Qt backend, and then imports and runs
`voronoi_qt.py`'s main window.
"""
import os
import sys
import importlib

# Ensure the script's directory is on sys.path so relative imports work
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

# Try to prefer PyQt6, then PyQt5
qt_binding = None
for candidate in ("PyQt6", "PyQt5"):
    try:
        importlib.import_module(candidate)
        qt_binding = candidate
        break
    except Exception:
        pass

if not qt_binding:
    print("ERROR: No PyQt6 or PyQt5 found. Install one of them (see requirements.txt).", file=sys.stderr)
    sys.exit(1)

# Set matplotlib backend to QtAgg early
import matplotlib
matplotlib.use("QtAgg")

# Run the GUI
try:
    import voronoi_qt
    voronoi_qt.main()
except Exception as e:
    print("Failed to start voronoi GUI:", e, file=sys.stderr)
    raise

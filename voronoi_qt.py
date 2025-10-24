#!/usr/bin/env python3
"""Standalone Voronoi + warp interactive app using PyQt and Matplotlib.

Uses PyQt6 if available, falls back to PyQt5. Renders the same Voronoi
that your notebook generates and provides two sliders for `scale` and `freq`.

Run with the project's venv python if you want to use the same environment:
"/path/to/.venv/bin/python" voronoi_qt.py
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
from noise import pnoise2

# Try PyQt6 then PyQt5
try:
    from PyQt6 import QtWidgets, QtCore
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    QtVersion = 6
except Exception:
    from PyQt5 import QtWidgets, QtCore
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    QtVersion = 5


def voronoi_polygons(vor):
    regions = []
    for region_index in vor.point_region:
        region = vor.regions[region_index]
        if -1 in region or len(region) == 0:
            continue
        poly = Polygon(vor.vertices[region])
        if poly.is_valid and poly.area > 0:
            regions.append(poly)
    return regions


def warp_vertices(poly, scale=0.05, freq=3.0):
    coords = np.array(poly.exterior.coords)
    warped = []
    for x, y in coords:
        dx = pnoise2(x * freq, y * freq)
        dy = pnoise2((x + 10) * freq, (y + 10) * freq)
        warped.append([x + dx * scale, y + dy * scale])
    return Polygon(warped)


def plot_polygons(ax, polys, title):
    ax.cla()
    for poly in polys:
        x, y = poly.exterior.xy
        ax.plot(x, y, 'k-', linewidth=1)
    ax.set_aspect('equal')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title)


class VoronoiWidget(QtWidgets.QWidget):
    def __init__(self, points=None, parent=None):
        super().__init__(parent)
        # --- Top controls: seed, number of points, Refresh button ---
        self.seed_spin = QtWidgets.QSpinBox()
        self.seed_spin.setRange(0, 2 ** 31 - 1)
        self.seed_spin.setValue(10)

        self.npoints_spin = QtWidgets.QSpinBox()
        self.npoints_spin.setRange(2, 2000)
        self.npoints_spin.setValue(20)

        self.refresh_btn = QtWidgets.QPushButton("Refresh")

        # Generate initial points using seed and npoints
        rng = np.random.RandomState(self.seed_spin.value())
        self.points = points if points is not None else rng.rand(self.npoints_spin.value(), 2)
        self.vor = Voronoi(self.points)
        self.polys = voronoi_polygons(self.vor)

        # Figure and canvas
        self.figure, self.axes = plt.subplots(1, 2, figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)

        # Sliders (use orientation compatible with PyQt5/6)
        if QtVersion == 6:
            orient = QtCore.Qt.Orientation.Horizontal
        else:
            orient = QtCore.Qt.Horizontal

        self.scale_slider = QtWidgets.QSlider(orient)
        # Use an integer slider with finer resolution: map 1..500 -> 0.001..0.5 (step = 0.001)
        self.scale_slider.setMinimum(1)
        self.scale_slider.setMaximum(500)
        # initial 0.10 -> 100/1000
        self.scale_slider.setValue(100)
        self.scale_slider.setTickInterval(10)
        try:
            self.scale_slider.setSingleStep(1)
            self.scale_slider.setPageStep(10)
        except Exception:
            pass

        self.freq_slider = QtWidgets.QSlider(orient)
        # Use int slider mapping 50..1000 -> 0.50..10.00 (step = 0.01)
        self.freq_slider.setMinimum(50)
        self.freq_slider.setMaximum(1000)
        # initial 5.0 -> 500/100
        self.freq_slider.setValue(500)
        self.freq_slider.setTickInterval(10)
        try:
            self.freq_slider.setSingleStep(1)
            self.freq_slider.setPageStep(10)
        except Exception:
            pass

        # Labels for sliders
        self.scale_label = QtWidgets.QLabel("Scale: 0.10")
        self.freq_label = QtWidgets.QLabel("Freq: 5.0")

        # Top layout (seed, npoints, refresh)
        top_controls = QtWidgets.QHBoxLayout()
        top_controls.addWidget(QtWidgets.QLabel("Seed:"))
        top_controls.addWidget(self.seed_spin)
        top_controls.addWidget(QtWidgets.QLabel("Points:"))
        top_controls.addWidget(self.npoints_spin)
        top_controls.addWidget(self.refresh_btn)

        # Slider layout (keeps sliders together)
        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(self.scale_label)
        controls.addWidget(self.scale_slider)
        controls.addWidget(self.freq_label)
        controls.addWidget(self.freq_slider)

        # Main layout: top controls above canvas and sliders
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_controls)
        layout.addWidget(self.canvas)
        layout.addLayout(controls)
        self.setLayout(layout)

        # Signals
        self.scale_slider.valueChanged.connect(self.on_slider_change)
        self.freq_slider.valueChanged.connect(self.on_slider_change)
        self.refresh_btn.clicked.connect(self.on_refresh)

        # Initial draw
        self.update_plot()

    def on_slider_change(self, value):
        # Map integer slider values back to floats with finer resolution
        scale = self.scale_slider.value() / 1000.0
        freq = self.freq_slider.value() / 100.0
        self.scale_label.setText(f"Scale: {scale:.2f}")
        self.freq_label.setText(f"Freq: {freq:.2f}")
        self.update_plot()

    def update_plot(self):
        scale = self.scale_slider.value() / 1000.0
        freq = self.freq_slider.value() / 100.0
        polys_warped = [warp_vertices(p, scale=scale, freq=freq) for p in self.polys]
        plot_polygons(self.axes[0], self.polys, "Original Voronoi")
        plot_polygons(self.axes[1], polys_warped, f"Warped (s={scale:.2f}, f={freq:.2f})")
        self.canvas.draw()

    def regenerate_points(self):
        """Regenerate random points using current seed and npoints."""
        seed = int(self.seed_spin.value())
        n = int(self.npoints_spin.value())
        rng = np.random.RandomState(seed)
        self.points = rng.rand(n, 2)
        self.vor = Voronoi(self.points)
        self.polys = voronoi_polygons(self.vor)

    def on_refresh(self):
        """Called when user presses Refresh: regenerate points and redraw once."""
        self.regenerate_points()
        # Do a single redraw with current slider values
        self.update_plot()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = VoronoiWidget()
    w.setWindowTitle("Voronoi Warper")
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Standalone Voronoi + warp interactive app using PyQt and Matplotlib.

This version integrates the robust backend logic for stable Voronoi
generation and polygon warping.
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box, MultiPolygon
from noise import pnoise2

try:
    from PyQt6 import QtWidgets, QtCore
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    QtVersion = 6
except Exception:
    from PyQt5 import QtWidgets, QtCore
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    QtVersion = 5


def voronoi_polygons(vor, bbox=box(0, 0, 1, 1)):
    regions = []
    for region_index in vor.point_region:
        region = vor.regions[region_index]
        if -1 in region or len(region) == 0:
            continue
        try:
            poly = Polygon(vor.vertices[region])
        except ValueError:
            continue
        if not poly.is_valid:
            poly = poly.buffer(0)
            if not poly.is_valid or poly.is_empty:
                continue
        clipped_poly = poly.intersection(bbox)
        if clipped_poly.is_empty:
            continue
        if isinstance(clipped_poly, Polygon):
            if clipped_poly.is_valid and clipped_poly.area > 0:
                regions.append(clipped_poly)
        elif isinstance(clipped_poly, MultiPolygon):
            for p in clipped_poly.geoms:
                if p.is_valid and p.area > 0:
                    regions.append(p)
    return regions


def warp_vertices(poly, scale=0.05, freq=3.0):
    if poly is None or poly.is_empty or not hasattr(poly, 'exterior'):
        return None
    coords = np.array(poly.exterior.coords)
    warped = []
    for x, y in coords:
        dx = pnoise2(x * freq, y * freq, octaves=2, persistence=0.5, lacunarity=2.0)
        dy = pnoise2((x + 10) * freq, (y + 10) * freq, octaves=2, persistence=0.5, lacunarity=2.0)
        warped.append([x + dx * scale, y + dy * scale])
    try:
        return Polygon(warped)
    except ValueError:
        return None


def plot_polygons(ax, polys, title):
    ax.cla()
    ax.set_aspect('equal')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])
    for poly in polys:
        if poly is None or poly.is_empty or not hasattr(poly, 'exterior'):
            continue
        x, y = poly.exterior.xy
        ax.plot(x, y, 'k-', linewidth=0.8)


class VoronoiWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bbox = box(0, 0, 1, 1)
        self.seed_spin = QtWidgets.QSpinBox()
        self.seed_spin.setRange(0, 2 ** 31 - 1)
        self.seed_spin.setValue(10)
        self.npoints_spin = QtWidgets.QSpinBox()
        self.npoints_spin.setRange(2, 2000)
        self.npoints_spin.setValue(20)
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.save_btn = QtWidgets.QPushButton("Save...")
        self.points = None
        self.vor = None
        self.polys = []
        self.figure, self.axes = plt.subplots(1, 2, figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        if QtVersion == 6:
            orient = QtCore.Qt.Orientation.Horizontal
        else:
            orient = QtCore.Qt.Horizontal
        self.scale_slider = QtWidgets.QSlider(orient)
        self.scale_slider.setMinimum(1)
        self.scale_slider.setMaximum(500)
        self.scale_slider.setValue(100)
        self.scale_slider.setTickInterval(10)
        try:
            self.scale_slider.setSingleStep(1)
            self.scale_slider.setPageStep(10)
        except Exception:
            pass
        self.freq_slider = QtWidgets.QSlider(orient)
        self.freq_slider.setMinimum(50)
        self.freq_slider.setMaximum(1000)
        self.freq_slider.setValue(500)
        self.freq_slider.setTickInterval(10)
        try:
            self.freq_slider.setSingleStep(1)
            self.freq_slider.setPageStep(10)
        except Exception:
            pass
        self.scale_label = QtWidgets.QLabel("Scale: 0.03")
        self.freq_label = QtWidgets.QLabel("Freq: 3.00")
        top_controls = QtWidgets.QHBoxLayout()
        top_controls.addWidget(QtWidgets.QLabel("Seed:"))
        top_controls.addWidget(self.seed_spin)
        top_controls.addWidget(QtWidgets.QLabel("Points:"))
        top_controls.addWidget(self.npoints_spin)
        top_controls.addWidget(self.refresh_btn)
        top_controls.addWidget(self.save_btn)
        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(self.scale_label)
        controls.addWidget(self.scale_slider)
        controls.addWidget(self.freq_label)
        controls.addWidget(self.freq_slider)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_controls)
        layout.addWidget(self.canvas)
        layout.addLayout(controls)
        self.setLayout(layout)
        self.scale_slider.valueChanged.connect(self.on_slider_change)
        self.freq_slider.valueChanged.connect(self.on_slider_change)
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.save_btn.clicked.connect(self.on_save)
        self.regenerate_points()
        self.update_plot()
        self.on_slider_change(0)

    def on_slider_change(self, value):
        scale = self.scale_slider.value() / 1000.0
        freq = self.freq_slider.value() / 100.0
        self.scale_label.setText(f"Scale: {scale:.3f}")
        self.freq_label.setText(f"Freq: {freq:.2f}")
        self.update_plot()

    def update_plot(self):
        scale = self.scale_slider.value() / 1000.0
        freq = self.freq_slider.value() / 100.0
        warped_polys = []
        for poly in self.polys:
            try:
                warped = warp_vertices(poly, scale=scale, freq=freq)
                if warped:
                    warped = warped.intersection(self.bbox)
                    if not warped.is_valid:
                        warped = warped.buffer(0)
                    if warped.is_empty:
                        continue
                    if isinstance(warped, Polygon):
                        warped_polys.append(warped)
                    elif isinstance(warped, MultiPolygon):
                        warped_polys.extend(p for p in warped.geoms if p.is_valid and p.area > 0)
            except Exception:
                continue
        plot_polygons(self.axes[0], self.polys, "Original Voronoi")
        plot_polygons(self.axes[1], warped_polys, f"Warped (s={scale:.3f}, f={freq:.2f})")
        self.canvas.draw()

    def regenerate_points(self):
        seed = int(self.seed_spin.value())
        n = int(self.npoints_spin.value())
        rng = np.random.RandomState(seed)
        self.points = rng.rand(n, 2)
        border_points = np.array(
            [[x, y] for x in [-1, 0, 1, 2] for y in [-1, 2]] +
            [[x, y] for x in [-1, 2] for y in [0, 1]]
        )
        all_points = np.vstack([self.points, border_points])
        try:
            self.vor = Voronoi(all_points)
        except Exception as e:
            print(f"Error creating Voronoi: {e}")
            QtWidgets.QMessageBox.critical(self, "Voronoi Error", f"Failed to generate Voronoi diagram:\n{e}")
            return
        self.polys = voronoi_polygons(self.vor, bbox=self.bbox)

    def on_refresh(self):
        self.regenerate_points()
        self.update_plot()

    def on_save(self):
        filters = "PNG Image (*.png);;SVG Image (*.svg);;PDF File (*.pdf)"
        options = QtWidgets.QFileDialog.Options()
        try:
            fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save figure", "voronoi.png", filters, options=options)
        except TypeError:
            fname = QtWidgets.QFileDialog.getSaveFileName(self, "Save figure", "voronoi.png", filters)
            if isinstance(fname, tuple):
                fname = fname[0]
        if not fname:
            return
        try:
            self.figure.savefig(fname, dpi=300, bbox_inches='tight')
            QtWidgets.QMessageBox.information(self, "Saved", f"Saved figure to:\n{fname}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save error", f"Failed to save figure:\n{e}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = VoronoiWidget()
    w.setWindowTitle("Voronoi Warper")
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

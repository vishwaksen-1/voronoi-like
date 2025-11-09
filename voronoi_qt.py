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


def plot_polygons(ax, polys, title, linewidth=0.8):
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
        ax.plot(x, y, 'k-', linewidth=linewidth)


def _save_single_svg(polys, title, out_path, fmt='svg', size=(6, 6), linewidth=0.8):
    """Render polygons onto a single-axis figure and save as SVG.

    This creates a temporary Matplotlib figure so we don't disturb the
    embedded GUI figure, renders the polygons with the same axis limits
    and aspect, saves to `out_path` (string or Path), and closes the
    temporary figure to free resources.
    """
    fig, ax = plt.subplots(1, 1, figsize=size)
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
        ax.plot(x, y, 'k-', linewidth=linewidth)
    try:
        actual_fmt = 'jpeg' if fmt == 'jpg' else fmt
        fig.savefig(str(out_path), format=actual_fmt, bbox_inches='tight')
    finally:
        plt.close(fig)


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
        self.linewidth_spin = QtWidgets.QDoubleSpinBox()
        self.linewidth_spin.setRange(0.1, 10.0)
        self.linewidth_spin.setSingleStep(0.1)
        self.linewidth_spin.setValue(0.8)
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(['svg', 'png', 'jpg'])
        # default to jpg
        idx = self.format_combo.findText('jpg')
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
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
        top_controls.addWidget(QtWidgets.QLabel("Line width:"))
        top_controls.addWidget(self.linewidth_spin)
        top_controls.addWidget(self.refresh_btn)
        top_controls.addWidget(self.save_btn)
        top_controls.addWidget(QtWidgets.QLabel("Format:"))
        top_controls.addWidget(self.format_combo)
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
        # update on linewidth change as well
        try:
            self.linewidth_spin.valueChanged.connect(self.update_plot)
        except Exception:
            pass
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
        lw = float(self.linewidth_spin.value()) if hasattr(self, 'linewidth_spin') else 0.8
        plot_polygons(self.axes[0], self.polys, "Original Voronoi", linewidth=lw)
        plot_polygons(self.axes[1], warped_polys, f"Warped (s={scale:.3f}, f={freq:.2f})", linewidth=lw)
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
        # Build timestamped save directory next to this script
        try:
            from pathlib import Path
            from datetime import datetime
        except Exception:
            QtWidgets.QMessageBox.critical(self, "Save error", "Required modules for saving are missing.")
            return
        script_dir = Path(__file__).resolve().parent
        now = datetime.now()
        folder_ts = now.strftime("%d_%m_%y_%H_%M")
        save_dir = script_dir / f"saved plots {folder_ts}"
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save error", f"Failed to create save directory:\n{e}")
            return

        # compute current warped polygons using present slider settings
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

        # Save original and warped separately using selected format
        fmt = 'svg'
        try:
            fmt = str(self.format_combo.currentText()).lower()
        except Exception:
            pass
        ts_file = now.strftime("%d_%m_%y_%H_%M_%S")
        orig_name = save_dir / f"Voronoi_original_{ts_file}.{fmt}"
        warped_name = save_dir / f"Voronoi_warped_{ts_file}.{fmt}"
        try:
            lw = float(self.linewidth_spin.value()) if hasattr(self, 'linewidth_spin') else 0.8
            _save_single_svg(self.polys, "Original Voronoi", orig_name, fmt=fmt, linewidth=lw)
            _save_single_svg(warped_polys, f"Warped (s={scale:.3f}, f={freq:.2f})", warped_name, fmt=fmt, linewidth=lw)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save error", f"Failed to save SVGs:\n{e}")
            return

        # Feedback to user
        try:
            self.setWindowTitle("Saved ✅")
            QtWidgets.QMessageBox.information(self, "Saved", f"Saved files:\n{orig_name}\n{warped_name}")
        except Exception:
            pass


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = VoronoiWidget()
    w.setWindowTitle("Voronoi Warper")
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

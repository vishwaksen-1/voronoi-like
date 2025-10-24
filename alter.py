import sys
import numpy as np
import matplotlib
# We no longer need to force the 'QtAgg' backend
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box, MultiPolygon
from noise import pnoise2

# --- All PyQt imports and the MainWindow class have been removed ---

def voronoi_polygons(vor, bbox=box(0, 0, 1, 1)):
    """
    Generates clipped and cleaned Shapely Polygons from a SciPy Voronoi object.
    
    Robustness improvements:
    1. Clips polygons to a bounding box.
    2. Repairs invalid polygons using .buffer(0).
    3. Handles MultiPolygon outputs from clipping.
    """
    regions = []
    for region_index in vor.point_region:
        region = vor.regions[region_index]
        
        # Skip infinite regions (indicated by -1) or empty regions
        if -1 in region or len(region) == 0:
            continue
            
        try:
            # Create the polygon from the region's vertices
            poly = Polygon(vor.vertices[region])
        except ValueError:
            # Can happen if vertices are collinear
            continue  # Skip this region

        # Repair invalid polygons (e.g., self-intersections)
        if not poly.is_valid:
            poly = poly.buffer(0)
            
            # Still invalid or became empty after buffer
            if not poly.is_valid or poly.is_empty:
                continue

        # Clip the polygon to the bounding box
        clipped_poly = poly.intersection(bbox)

        # Handle the result of the intersection
        if clipped_poly.is_empty:
            continue
        
        if isinstance(clipped_poly, Polygon):
            # Simple case: intersection is a single, valid polygon
            if clipped_poly.is_valid and clipped_poly.area > 0:
                regions.append(clipped_poly)
                
        elif isinstance(clipped_poly, MultiPolygon):
            # Complex case: intersection is multiple polygons
            for p in clipped_poly.geoms:  # Use .geoms to iterate
                if p.is_valid and p.area > 0:
                    regions.append(p)
                    
    return regions


# --- Helper functions for densification have been removed ---

def warp_vertices(poly, scale=0.05, freq=3.0):
    """Applies Perlin noise displacement to polygon vertices."""
    if poly is None or poly.is_empty or not hasattr(poly, 'exterior'):
        return None
        
    coords = np.array(poly.exterior.coords)
    warped = []
    for x, y in coords:
        # Get noise values
        dx = pnoise2(x * freq, y * freq, octaves=2, persistence=0.5, lacunarity=2.0)
        dy = pnoise2((x + 10) * freq, (y + 10) * freq, octaves=2, persistence=0.5, lacunarity=2.0)
        # Apply scaled displacement
        warped.append([x + dx * scale, y + dy * scale])
        
    try:
        return Polygon(warped)
    except ValueError:
        return None  # Failed to create polygon


def plot_polygons(ax, polys, title, points=None, fill=True):
    """
    Helper function to plot a list of polygons on an axis.
    
    Improvements:
    1. Fills polygons with color.
    2. Renders polygon holes (by filling them with white).
    3. Can optionally plot the generator points.
    """
    ax.cla()  # Clear the axis
    ax.set_aspect('equal')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_xticks([])  # Hide tick marks
    ax.set_yticks([])
    
    # --- Set fill properties ---
    facecolor = 'lightgray' if fill else 'none'
    alpha = 0.6 if fill else 1.0

    for poly in polys:
        if poly is None or poly.is_empty or not hasattr(poly, 'exterior'):
            continue
            
        # --- Plot the exterior shell ---
        x, y = poly.exterior.xy
        ax.fill(x, y, facecolor=facecolor, alpha=alpha, edgecolor='black', linewidth=0.8)

        # --- Plot the interior holes ---
        # We fill holes with white to "cut them out" visually
        for interior in poly.interiors:
            hx, hy = interior.xy
            ax.fill(hx, hy, facecolor='white', edgecolor='black', linewidth=0.8)

    # --- Plot generator points on top ---
    if points is not None:
        # Only plot points that are within the 0-1 bounding box
        valid_points = points[(points[:, 0] >= 0) & (points[:, 0] <= 1) &
                              (points[:, 1] >= 0) & (points[:, 1] <= 1)]
        ax.scatter(valid_points[:, 0], valid_points[:, 1], 
                   c='red', s=8, zorder=10, label='Generators', alpha=0.7)
        
        # Only show legend if points were actually plotted
        if len(valid_points) > 0:
            # Place legend outside the plot
            ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1.05))


    
if __name__ == "__main__":
    # --- Example usage of the backend engine ---
    
    # 1. Define parameters
    num_points = 10
    scale = 0.5
    freq = 3.0
    # densify_length parameter removed

    print(f"Generating plot with {num_points} points, scale={scale}, freq={freq}")

    # 2. Generate points and Voronoi diagram
    points = np.random.rand(num_points, 2)
    border_points = np.array(
        [[x, y] for x in [-1, 0, 1, 2] for y in [-1, 2]] +
        [[x, y] for x in [-1, 2] for y in [0, 1]]
    )
    all_points = np.vstack([points, border_points])

    try:
        vor = Voronoi(all_points)
    except Exception as e:
        print(f"Error creating Voronoi: {e}")
        sys.exit(1)

    # 3. Define bounding box
    bbox = box(0, 0, 1, 1)

    # 4. Get original polygons
    polys = voronoi_polygons(vor, bbox)

    # 5. Get warped polygons
    warped_polys = []
    for poly in polys:
        try:
            # Pass the new densify_length parameter
            warped = warp_vertices(poly, scale=scale, freq=freq) # Removed densify_length
            
            # Post-warp clipping and cleaning
            if warped: # Check if warped is not None
                warped = warped.intersection(bbox)
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

    # 6. Plot the results using Matplotlib
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Pass the generator points to the plotting function
    plot_polygons(ax1, polys, f"Original Voronoi ({num_points} points)", points=points, fill=True)
    plot_polygons(ax2, warped_polys, f"Warped (Scale: {scale:.3f}, Freq: {freq:.1f})", points=points, fill=True) # Removed densify from title

    fig.tight_layout()
    print("Displaying plot...")
    plt.show()


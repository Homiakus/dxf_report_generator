import os
import math
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing import matplotlib as ezdxf_matplotlib
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union, linemerge, polygonize

def calculate_total_length(doc):
    total_length = 0.0
    msp = doc.modelspace()
    for entity in msp:
        try:
            length = 0.0
            if entity.dxftype() == 'LINE':
                length = calculate_line_length(entity)
            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                length = calculate_polyline_length(entity)
            elif entity.dxftype() == 'CIRCLE':
                length = calculate_circle_length(entity)
            elif entity.dxftype() == 'ARC':
                length = calculate_arc_length(entity)
            elif entity.dxftype() == 'SPLINE':
                length = calculate_spline_length(entity)
            total_length += length
        except Exception as e:
            print(f"Error processing {entity.dxftype()}: {e}")
            continue
    return total_length

def calculate_line_length(entity):
    start = entity.dxf.start
    end = entity.dxf.end
    return math.hypot(end[0] - start[0], end[1] - start[1])

def calculate_polyline_length(entity):
    length = 0.0
    points = list(entity.get_points())
    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]
        length += math.hypot(end[0] - start[0], end[1] - start[1])
    if entity.closed:
        start = points[-1]
        end = points[0]
        length += math.hypot(end[0] - start[0], end[1] - start[1])
    return length

def calculate_circle_length(entity):
    return 2 * math.pi * entity.dxf.radius

def calculate_arc_length(entity):
    radius = entity.dxf.radius
    start_angle = math.radians(entity.dxf.start_angle)
    end_angle = math.radians(entity.dxf.end_angle)
    angle = end_angle - start_angle
    if angle < 0:
        angle += 2 * math.pi
    return radius * angle

def calculate_spline_length(entity):
    length = 0.0
    spline_points = entity.approximate(segments=100)
    for i in range(len(spline_points) - 1):
        start = spline_points[i]
        end = spline_points[i + 1]
        length += math.hypot(end[0] - start[0], end[1] - start[1])
    return length

def get_entity_vertices(entity):
    vertices = []
    if entity.dxftype() == 'LINE':
        vertices.extend([entity.dxf.start[:2], entity.dxf.end[:2]])
    elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
        vertices.extend([point[:2] for point in entity.get_points()])
    elif entity.dxftype() == 'CIRCLE':
        center = entity.dxf.center
        radius = entity.dxf.radius
        # Use more points for precise circle approximation (e.g., 64 points)
        num_points = 64
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            vertices.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
        vertices.append(vertices[0]) # Close it
    elif entity.dxftype() == 'ARC':
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = math.radians(entity.dxf.start_angle)
        end_angle = math.radians(entity.dxf.end_angle)
        if end_angle < start_angle:
            end_angle += 2 * math.pi
        num_points = 32
        for i in range(num_points + 1):
            angle = start_angle + (end_angle - start_angle) * i / num_points
            vertices.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
    elif entity.dxftype() == 'SPLINE':
        spline_points = entity.approximate(segments=100)
        vertices.extend([(p[0], p[1]) for p in spline_points])
    return vertices

def calculate_precise_area(doc):
    """
    Calculates precise area of closed shapes using Shapely.
    Works by collecting all segments, merging them into linestrings,
    polygonizing them, and subtracting interior holes.
    """
    msp = doc.modelspace()
    lines = []
    polygons = []

    for entity in msp:
        try:
            vertices = get_entity_vertices(entity)
            if len(vertices) >= 2:
                lines.append(LineString(vertices))
            elif entity.dxftype() == 'CIRCLE':
                # Circle might be returned as one closed loop > 2 vertices by get_entity_vertices now
                poly = Polygon(vertices)
                if poly.is_valid and not poly.is_empty:
                    polygons.append(poly)
        except Exception as e:
            print(f"Error processing {entity.dxftype()} for area: {e}")
            continue

    if lines:
        merged = linemerge(lines)
        if hasattr(merged, 'geoms'):
            poly_geoms = list(polygonize(merged.geoms))
        else:
            poly_geoms = list(polygonize([merged]))

        for p in poly_geoms:
            if not p.is_valid:
                p = p.buffer(0)
            if p.geom_type == 'Polygon':
                polygons.append(p)
            elif p.geom_type == 'MultiPolygon':
                polygons.extend(p.geoms)

    if not polygons:
        return 0.0

    # Sort polygons by area, largest first
    polygons.sort(key=lambda p: p.area, reverse=True)

    outer_boundary = polygons[0]
    total_area = outer_boundary.area

    # Subtract inner holes
    for inner_poly in polygons[1:]:
        # If the inner polygon is completely contained within the outer boundary
        if outer_boundary.contains(inner_poly) or outer_boundary.intersection(inner_poly).area > 0.9 * inner_poly.area:
            total_area -= inner_poly.area

    return total_area / 1_000_000  # Convert mm^2 to m^2

def analyze_dxf_artifacts(doc, min_length=0.1):
    """
    Analyzes the DXF document for potential artifacts like micro-segments
    and unclosed contours which might cause issues during cutting.
    """
    msp = doc.modelspace()
    micro_segments = 0
    lines = []

    for entity in msp:
        try:
            # 1. Check for micro-segments
            length = 0.0
            if entity.dxftype() == 'LINE':
                length = calculate_line_length(entity)
            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                length = calculate_polyline_length(entity)
            elif entity.dxftype() == 'CIRCLE':
                length = calculate_circle_length(entity)
            elif entity.dxftype() == 'ARC':
                length = calculate_arc_length(entity)
            elif entity.dxftype() == 'SPLINE':
                length = calculate_spline_length(entity)

            if 0 < length < min_length:
                micro_segments += 1

            # 2. Collect lines for unclosed contour analysis
            vertices = get_entity_vertices(entity)
            if len(vertices) >= 2:
                lines.append(LineString(vertices))
        except Exception:
            continue

    unclosed_contours = 0
    if lines:
        merged = linemerge(lines)
        geoms = merged.geoms if hasattr(merged, 'geoms') else [merged]
        for geom in geoms:
            # If after merging it is a LineString but not a closed ring
            if geom.geom_type == 'LineString' and not geom.is_ring:
                unclosed_contours += 1

    warnings = []
    if micro_segments > 0:
        warnings.append(f"Обнаружено {micro_segments} микро-сегментов (< {min_length}мм).")
    if unclosed_contours > 0:
        warnings.append(f"Обнаружено {unclosed_contours} незамкнутых контуров.")

    return warnings

def render_dxf_to_image(doc, image_path):
    try:
        # Save exact plot to image using matplotlib and ezdxf
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        out = ezdxf_matplotlib.MatplotlibBackend(ax)

        # set white background and black foreground
        ctx.current_layout.set_colors(bg="#FFFFFF", fg="#000000")

        Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
        fig.savefig(image_path, dpi=300)
        plt.close(fig)
        return True
    except Exception as e:
        print(f"Error rendering DXF to image: {e}")
        return False

def parse_filename_metadata(filename):
    """
    Parses filename to extract metadata.
    Expected format: name_material_thickness_quantity.dxf
    Fallback to standard name_quantity.dxf or just name.dxf
    """
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split('_')

    metadata = {
        'name': base_name,
        'material': 'N/A',
        'thickness': 'N/A',
        'quantity': 1
    }

    if len(parts) >= 4 and parts[-1].isdigit():
        metadata['quantity'] = int(parts[-1])
        metadata['thickness'] = parts[-2]
        metadata['material'] = parts[-3]
        metadata['name'] = '_'.join(parts[:-3])
    elif len(parts) >= 2 and parts[-1].isdigit():
        metadata['quantity'] = int(parts[-1])
        metadata['name'] = '_'.join(parts[:-1])

    return metadata

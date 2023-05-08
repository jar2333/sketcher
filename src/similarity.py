from shapely import Polygon, MultiPolygon, MultiPolygon

from typing import List, Tuple

def graph_similarity(polygon_pairs : List[Tuple[Polygon, Polygon]]):
    s = 0.0
    for p1, p2 in polygon_pairs:
        s += polygon_similarity(p1, p2)

    return s / len(polygon_pairs)

def polygon_similarity(p1: Polygon, p2: Polygon):

    hull = MultiPolygon([p1, p2]).convex_hull

    min_area = min(p1.area, p2.area)
    hull_area = hull.area

    return min_area / hull_area

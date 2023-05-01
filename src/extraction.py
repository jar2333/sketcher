import networkx as nx

import matplotlib.pyplot as plt

import shapely

from itertools import product, combinations

from numpy import array

DEFAULT_STEP = 10

"""
----------------------------
-- GRAPH EXTRACTION (on-line)
----------------------------
"""

def extract_graph(paths, label, step=DEFAULT_STEP) -> nx.Graph:
    """
    Extract topology and geometry graph from source (image, label) pair.
    
    Nodes signify visual units in the image. These include:
    - Strokes (lines, curves)
    - Shapes (circle, rectangle)
    
    Nodes contain data, including:
    - Shape information
    - Center of unit in image coordinates
    
    Edges specify spatial relationships between nodes, as per 
    Sousa & Fonseca. “Sketch-Based Retrieval of Drawings using Topological Proximity” :
    - Adjacency: two nodes intersect
    - Composition: a node is contained inside another
    """
    G = nx.Graph()
    
    # Get sketch line strings
    line_strings = get_line_strings(paths, step=step)
    
    # Use contour centroids to get node
    centroids = get_centroids(line_strings)
    
    # Use hull to derive adjacency relations
    polygons = get_polygons(line_strings)
    
    # Create nodes with the following features:
    # - centroid
    # - number of vertices
    # - perimeter 
    # - area  
    # - bounding box area
    # - bounding circle radius
    for i, c in enumerate(centroids):
        if polygons[i] is not None:
            length = polygons[i].length
            area   = polygons[i].area 

            radius = shapely.minimum_bounding_radius(polygons[i])
            
            minx, miny, maxx, maxy = polygons[i].bounds
            bounds = (maxx - minx)*(maxy - miny)
            
            num_vertices = (set(polygons[i].boundary.coords))
            
            G.add_node(i, 
                       position=(c.x, c.y),
                       vertices=num_vertices,
                       length=length,
                       area=area,
                       radius=radius,
                       bounds=bounds
                      )
    
    # Create neighbor edges using convex hull intersection
    for i, j in combinations(G.nodes, 2):
        h1, h2 = polygons[i], polygons[j]
        if i != j and h1 is not None and h2 is not None:
            if h1.intersects(h2):
                G.add_edge(i, j, relation='neighbor')
            elif h1.contains(h2):
                G.add_edge(i, j, relation='parent')
                
    # Add graph labels
    G.graph['label'] = label

    # Use python kwargs?
    # G.graph['filename'] = svg['filename']
    
    return G

"""
----------------------------
-- PLOTTING
----------------------------
"""

def plot_graph(G):
    """
    Plot extracted graph.
    """
    pos = nx.get_node_attributes(G,'position')
    
    fig = plt.figure()
    
    title = 'Topology graph' 
    plt.title(title)
    
    nx.draw(
        G, pos, edge_color='black', width=1, linewidths=1,
        node_size=500, node_color='blue', alpha=0.5
    )
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=nx.get_edge_attributes(G,'relation'),
        font_color='red'
    )
    
    # plt.axis('off')

    plt.gca().invert_yaxis()

    return fig

def plot_polygons(polygons):
    fig = plt.figure()
    
    title = 'Polygons'
    plt.title(title)

    for p in polygons:
        if p is None:
            continue

        x,y = p.exterior.xy
        plt.plot(x,y)

    plt.gca().invert_yaxis()

    return fig

def plot_line_strings(line_strings):
    fig = plt.figure()
    
    title = 'Line strings'
    plt.title(title)

    for ls in line_strings:
        x, y = ls.coords.xy
        plt.plot(x, y)

    plt.gca().invert_yaxis()

    return fig


"""
----------------------------
-- POINT TO LINESTRING PROCESSING
----------------------------
"""

def get_line_strings(paths, step=DEFAULT_STEP):
    """
    Converts the paths (list of lists of points) to line strings.
    """
    line_strings = []

    for path in paths:
        sp = snap_round(path, step)
        
        ls = to_line_string(sp)

        line_strings.append(ls)
        
    return line_strings

def snap_round(path_points, step=DEFAULT_STEP):
    """
    The snap round algorithm: line segments to a fixed precision grid.
    """
    return (array(path_points)//step)*step


def to_line_string(path_points):
    """
    Converts a list of lists of control points to a shapely LineString
    """
    return shapely.LineString(path_points)

def filter_line_strings(line_strings):
    """
    Filter out all linestrings that are insignificant.
    """
    return line_strings


"""
----------------------------
-- ANALYZE/PROCESS LINESTRINGS
----------------------------
"""

def get_centroids(line_strings):
    """
    Get the centroids of a given line string.
    """
    return [ls.centroid for ls in line_strings]


def get_hulls(line_strings):
    """
    Get the convex hulls of the given line strings.
    """
    
    hulls = []
    
    for ls in line_strings:
        hull = ls.convex_hull
        if ls.length > 0 and isinstance(hull, shapely.Polygon):
            hulls.append(hull)
        else:
            hulls.append(None)
            
    return hulls

def filter_polygons(polygons):
    """
    Filter out all convex hulls that are insignificant, implemented
    as the area being smaller than a certain threshold, (20*20)*4
    """
    return [p if p is not None and p.area > 400*4 else None for p in polygons ]

def get_polygons(line_strings):
    """
    Returns the polygons created by the list of line strings.

    Follows the procedure described in Fonseca et al. "Content-based retrieval of technical drawings".

    - Convert the initial drawing or sketch in a set of line segments and simplify those.
    - Detect line segment intersections and remove them by replacing intersected segments by their subsegments that contain no intersections. 
    - Create a graph induced by the non-intersecting line segments, where nodes represent endpoints or proper intersection points of original line segments and edges.
    - Compute the Minimum Cycle Basis (MCB) of the induced graph.
    - Construct a set of polygons from cycles in the MCB and discard small polygons.

    Uses the linestring intersection detection code from: https://gis.stackexchange.com/a/423405
    """
    def add_edge_ifneq(g, a, b):
        if a != b:
            g.add_edge(a,b)
            
    # Process "near-polygons" first
            
    segments = []
    for ls in line_strings:
        segments += get_segments(detect_approximate_polygon(ls))
        
    g = nx.Graph()
    
    for seg1,seg2 in combinations(segments,2):
        if seg1.intersects(seg2):
            inter = seg1.intersection(seg2)
            
            s1, t1 = get_endpoints(seg1)
            s2, t2 = get_endpoints(seg2)

            if isinstance(inter, shapely.Point):  
                g.add_nodes_from([s1, s2, t1, t2, inter])
                
                add_edge_ifneq(g, s1, inter)
                add_edge_ifneq(g, s2, inter)
                add_edge_ifneq(g, inter, t1)
                add_edge_ifneq(g, inter, t2)
            else:
                i1, i2 = inter.coords
                
                g.add_nodes_from([s1, s2, t1, t2, i1, i2])
                
                # idk about edges in this case :(
            
    cycles = nx.minimum_cycle_basis(g)

    polygons = []
    for c in cycles:
        lsc = shapely.LineString(c)
        hull = lsc.convex_hull
        if isinstance(hull, shapely.Polygon):
            polygons.append(hull) 

    return polygons

def detect_approximate_polygon(ls):
    s, t = get_endpoints(ls)
    
    # If the two end points are very close relative 
    # to the total length of the linestring, return a closed linestring
    if s != t and s.distance(t) < ls.length / 10:
        ring = shapely.LineString(list(ls.coords) + [t, s])
        return ring
    
    # else, return input unmodified
    return ls

def get_endpoints(ls):
    """
    Gets the endpoints of a line string
    """
    return ls.interpolate(0, normalized=True), ls.interpolate(1, normalized=True)

def get_segments(ls):
    segments = map(shapely.LineString, zip(ls.coords[:-1], ls.coords[1:]))
    return [s for s in segments if s.coords[0] != s.coords[1]]
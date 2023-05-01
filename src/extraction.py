import networkx as nx

import matplotlib.pyplot as plt

import shapely

from itertools import product

from numpy import array

"""
----------------------------
-- GRAPH EXTRACTION (on-line)
----------------------------
"""

def extract_graph(paths, label, step=10) -> nx.Graph:
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
    hulls = get_hulls(line_strings)
    
    # Create nodes with the following features:
    # - centroid
    # - number of vertices
    # - perimeter 
    # - area  
    # - bounding box area
    # - bounding circle radius
    for i, c in enumerate(centroids):
        if hulls[i] is not None:
            length = hulls[i].length
            area   = hulls[i].area 
            
            radius = shapely.minimum_bounding_radius(hulls[i])
            
            minx, miny, maxx, maxy = hulls[i].bounds
            bounds = (maxx - minx)*(maxy - miny)
            
            num_vertices = (set(hulls[i].boundary.coords))
            
            G.add_node(i, 
                       position=(c.x, c.y),
                       vertices=num_vertices,
                       length=length,
                       area=area,
                       radius=radius,
                       bounds=bounds
                      )
    
    # Create neighbor edges using convex hull intersection
    for i, j in product(G.nodes, repeat=2):
        h1, h2 = hulls[i], hulls[j]
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

def plot_graph(G):
    """
    Plot extracted graph.
    """
    pos = nx.get_node_attributes(G,'position')
    
    fig = plt.figure()
    

    title = 'Topology graph' # G.graph['filename']
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
    
    plt.axis('off')

    return fig
    #plt.show()

def plot_polygons(polygons):
    fig = plt.figure()
    
    title = 'Polygons'
    plt.title(title)

    for p in polygons:
        x,y = p.exterior.xy
        plt.plot(x,y)

    return fig

def plot_line_strings(line_strings):
    fig = plt.figure()
    
    title = 'Line strings'
    plt.title(title)

    for ls in line_strings:
        x, y = ls.coords.xy
        plt.plot(x, y)

    return fig


"""
----------------------------
-- POINT TO LINESTRING PROCESSING
----------------------------
"""

def get_line_strings(paths, step=10):
    """
    Converts the paths (list of lists of points) to line strings.
    """
    line_strings = []

    for path in paths:
        sp = snap_round(path, step)
        
        ls = to_line_string(sp)

        line_strings.append(ls)
        
    return line_strings

def snap_round(path_points, step=20):
    """
    The snap round algorithm: line segments to a fixed precision grid.
    """
    return (array(path_points)//step)*step


def to_line_string(path_points):
    """
    Converts a list of lists of control points to a shapely LineString
    """
    return shapely.LineString(path_points)

# def filter_linestrings(linestrings):
#     """
#     Filter out all linestrings that are insignificant, implemented
#     as the length being smaller than a certain threshold, 400*2
#     """
#     return [l for l in linestrings if l.length > 20*2]

# def get_polygon(ls) -> shapely.Polygon:
#     s = ls.interpolate(0, normalized=True)
#     t = ls.interpolate(1, normalized=True)

#     if ls.length > 0 and s.distance(t)/ls.length < 0.5:
#         return shapely.polygonize([ls, shapely.LineString([s, t])])
    
#     return None

# def detect_polygons(line_strings):
#     """
#     Detect polygons in the image, from each singular linestring.
    
#     Compares the length of the linestring with the distance of the start and end points.
#     """

#     return [p for ls in line_strings if (p := get_polygon(ls)) != None ]

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

def get_polygons(line_strings):
    """
    Extracts polygons from the input strokes.

    TO-DO: IMPLEMENT.
    """
    return get_hulls(line_strings)


def filter_polygons(polygons, area):
    """
    Filter out all convex hulls that are insignificant, implemented
    as the area being smaller than a certain threshold, 400*2
    """
    return [p if p is not None and ((p.area / area)*(800**2))/(20**2) > 6 else None for p in polygons ]


"""
----------------------------
-- GRAPH EXTRACTION (off-line)
----------------------------
"""

def extract_graphs(images):
    """
    Extract all graphs from given images.
    """
    i = 0
    graphs = []
    for img, l in images:
        graphs.append(extract_graph(img, l))
        print(i)
        i += 1
    return graphs
import numpy as np

import networkx as nx

import pygmtools as pygm

import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch

import functools
from typing import Optional, Tuple

# from sklearn.decomposition import PCA as PCAdimReduc
from sklearn.feature_extraction import DictVectorizer

pygm.BACKEND = 'numpy' # set numpy as backend for pygmtools


def match(graph1, graph2) -> np.array:
    """
    Uses a graph match solver to find a match between two topological feature graphs.
    
    Uses the Quadratic Assignment Problem formulation of graph matching to encode graphs.
    
    The solver and parameters utilized are an implementation detail in this function.
    """
    K = build_affinity(graph1, graph2)
    X = pygm.rrwm(K, graph1.number_of_nodes(), graph2.number_of_nodes())
    return pygm.hungarian(X)


def build_affinity(graph1, graph2) -> np.array:
    """
    Construct affinity matrix for matching QAP solver.
    """
    node1, edge1, conn1 = encode(graph1)
    node2, edge2, conn2 = encode(graph2)
    
    gaussian_aff = functools.partial(pygm.utils.gaussian_aff_fn, sigma=1) # set affinity function
    
    return pygm.utils.build_aff_mat(node1, edge1, conn1, node2, edge2, conn2, edge_aff_fn=gaussian_aff)

def encode(graph) -> Tuple[np.array, np.array, np.array]:
    """
    Encode graph as a edge feature matrix, and node feature matrix, 
    connectivity matrix triple. This is fed to a QAP solver to match graphs.
    
    """
    # Extract array node features
    n_f = extract_node_features(graph)
    
    # Extract adjacency matrix edge features
    e_f = extract_edge_features(graph)
    
    # Derive connectivity matrix and edge features array from adjacency matrix edge features
    conn, edge = pygm.utils.dense_to_sparse(e_f)
    
    return n_f, edge, conn


def extract_edge_features(graph) -> np.array:
    """
    Extract edge features in the form of an adjacency matrix with an extra feature vector axis.
    
    Can utilize any of the input graph's graph, node, and edge labels to derive features.
    
    Can utilize scikit-learn's feature extraction to vectorize discrete and continuous features:
    https://scikit-learn.org/stable/modules/feature_extraction.html
    """
    # Get adjacency matrix from graph
    A = nx.to_numpy_array(graph)

    if not np.any(A): # if all zeros
        return A
    
    # ----------------
    # Length feature
    # ----------------
    
    # Get a 'positions' graph attribute:
    pos = nx.get_node_attributes(graph,'position')
    
    # Convert position dictionary to numpy array
    pos_arr = position_array(pos)

    # Derive edge distances from adjacency matrix
    A = ((np.expand_dims(pos_arr, 1) - np.expand_dims(pos_arr, 2)) ** 2).sum(axis=0) * A
    A = (A / A.max()).astype(np.float32)
    
    return A


def extract_node_features(graph) -> Optional[np.array]:
    """
    Extract node features in the form of an array of feature vectors.
    
    Can return None to indicate no node features.
    
    Can utilize any of the input graph's graph, node, and edge labels to derive features.
    
    Can utilize scikit-learn's feature extraction to vectorize discrete and continuous features:
    https://scikit-learn.org/stable/modules/feature_extraction.html
    """
    if graph.number_of_nodes() == 0:
        return None
    
    vec = DictVectorizer()

    measurements = []
    for _, attribs in graph.nodes.items():
        attribs = dict(attribs)
        a = {f: val for f, val in attribs.items() if f != 'vertices' and f != 'position'}

        c = attribs['position']
        a["x"] = c[0]
        a["y"] = c[1]

        measurements.append(a)

    return vec.fit_transform(measurements).toarray()


def position_array(pos):
    return np.array(list(pos.values())).T


def plot_match_graph(G, color='k'):
    """
    Plots a given graph with a 'positions' attribute.
    """
    A = nx.to_numpy_array(G)
    if 'positions' in G.graph:
        pos = G.graph['positions']
    else:
        pos = nx.get_node_attributes(G,'position')

    pts = position_array(pos)
    plt.scatter(pts[0], pts[1], c='w', edgecolors=color)

    for x, y in zip(np.nonzero(A)[0], np.nonzero(A)[1]):
        plt.plot((pts[0, x], pts[0, y]), (pts[1, x], pts[1, y]), color+'-')

def mapping_to_list(X, G1, G2):
    """
    Converts a mapping matrix returned by the match solver into a list of matched pairs
    """
    vertices1 = list(G1.nodes)
    vertices2 = list(G2.nodes)

    pairs = []

    for i in range(X.shape[0]): # Assumes 0th axis is G1
        j = np.argmax(X[i]).item()

        u, v = vertices1[i], vertices2[j]

        pairs.append((u, v))

    return pairs

def plot_mapping(X, graph1, graph2):
    pos1 = nx.get_node_attributes(graph1,'position')
    pos2 = nx.get_node_attributes(graph2,'position')
    
    plt.figure(figsize=(8, 4))
    plt.suptitle('Image Matching Result by RRWM')

    ax1 = plt.subplot(1, 2, 1)
    plot_match_graph(graph1)

    ax2 = plt.subplot(1, 2, 2)
    plot_match_graph(graph2)

    pts1 = position_array(pos1)
    pts2 = position_array(pos2)
    
    for i in range(X.shape[0]):
        j = np.argmax(X[i]).item()
        con = ConnectionPatch(xyA=pts1[:, i], xyB=pts2[:, j], coordsA="data", coordsB="data",
                              axesA=ax1, axesB=ax2, color="red" if i != j else "green")
        plt.gca().add_artist(con)
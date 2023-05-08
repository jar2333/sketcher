import numpy as np

from scipy import linalg

import networkx as nx

from scipy.spatial import KDTree

import pickle

from collections import defaultdict


DATABASE_FILENAME = "db/graphs.db"

DESCRIPTOR_SIZE = 7

"""
------------------------------
-- On-line functions 
-- (open, query, close)
------------------------------
"""

class Database:
    """
    A database.
    """

    def __init__(self, kv, filename=DATABASE_FILENAME):
        """
        Creates a database:
        - A resource handle for an in-disk B+-tree
        - An in-memory KD-tree for querying K nearest neighbors, constructed using keys in B+-tree
        """
        self.filename = filename
        self.kv = kv

        descriptors = []
        for d in self.kv:
            descriptors.append(np.frombuffer(d, dtype=float))

        assert len(descriptors) > 0
        
        self.descriptors = np.array(descriptors)

        self.kdtree = KDTree(self.descriptors)

    def query(self, query_graph, K=50, top=5):
        """
        Returns the label from the database using a query graph.
        """
        key = descriptor(query_graph, N=DESCRIPTOR_SIZE)

        # Query KD-tree for nearest descriptors
        dd, ii = self.kdtree.query(key, k=K)

        # Get the features of the neighbors
        neighbor_features = []
        for i in ii:
            k = self.descriptors[i]
            features = self.kv[bytes(k)] # returns list of feature, label pairs
            neighbor_features.append(features)

        return neighbor_features
    
    def close(self):
        """
        Closes database.
        """
        self.checkpoint()

    def checkpoint(self):
        """
        Saves db to disk
        """
        with open(self.filename, 'wb') as f:
            pickle.dump(self, f)

    def insert(self, k: np.array, v):
        self.kv[bytes(k)].append(v)

    def delete(self, k: np.array):
        del self.kv[bytes(k)]
    
def open_database(filename=DATABASE_FILENAME) -> Database:
    """
    Create db, with key_size of 8 bytes (C double) times vector size, 
    Other parameters to be determined
    """
    with open(filename, 'rb') as f:
        return pickle.load(f)

def query_database(db, query, K=50, top=5):
    """
    Returns the label from the database using a query graph.
    """
    return db.query(query, K=K, top=top)

def close_database(db):
    """
    Closes database.
    """
    db.close()


"""
------------------------------
-- Off-line functions: 
-- (construction, deletion) 
------------------------------
"""

def construct_database(descriptors, features):
    """
    Populates database with all graphs extracted from images, using graph descriptors as keys.
    
    Uses the algorithms described in Fonseca and Jorge "Indexing High-Dimensional Data for 
    Content-Based Retrieval in Large Databases".
    """
    # Create base dictionary
    kv = defaultdict(list)

    for k, v in zip(descriptors, features):
        kv[bytes(k)].append(v)

    # Create new Database    
    db =  Database(kv) 

    # Flush to disk
    db.checkpoint()

    return db
        

"""
------------------------------
-- Database index 
-- (descriptor, serialization)
------------------------------
"""

def descriptor(graph, N=DESCRIPTOR_SIZE):
    """
    Get the topology descriptor of the graph, as described in 
    Sousa and Fonseca "Sketch-Based Retrieval of Drawings using Topological Proximity"
    and in Fonseca and Jorge "Indexing High-Dimensional Data for Content-Based Retrieval 
    in Large Databases".
    
    Is the sorted array of absolute value eigenvalues of the graph's adjacency matrix.
    
    This is used to query a KD tree to find the K nearest neighbors of a topology descriptor.
    
    Additionally, it is used to query a B+-tree to find precomputed graph data/features on disk.
    
    It is padded with zeroes to a certain max length if the descriptor is less than.
    
    This N is calculated as either a max or, more flexibly, as a percentile (99.9%, for example).
    """
    # Get adjacency matrix of graph
    A = nx.to_numpy_array(graph)
    
    if A.size == 0:
        return np.zeros(N)
    
    # Compute absolute values of eigenvalues 
    spectra = -np.sort(-np.absolute(linalg.eigvals(A)))
    
    assert graph.number_of_nodes() == spectra.size
    
    if N >= spectra.size:
        # Pad with 0s
        return np.pad(spectra, (0, N - spectra.size), 'constant')
    else:
        # Truncate
        return spectra[:N]
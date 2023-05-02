import numpy as np

from scipy import linalg

import networkx as nx

from bplustree import BPlusTree
from bplustree.serializer import Serializer
from bplustree.node import Node

import os, errno

import random

from scipy.spatial import KDTree

from collections import Counter


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

    def __init__(self, bplustree):
        """
        Creates a database:
        - A resource handle for an in-disk B+-tree
        - An in-memory KD-tree for querying K nearest neighbors, constructed using keys in B+-tree
        """
        self.bplustree = bplustree

        descriptors = []
        try:
            for d in bplustree:
                descriptors.append(np.array(d))
        except: #StopIteration:
            assert len(descriptors) > 0
            
            self.descriptors = np.array(descriptors)
            self.kdtree = KDTree(self.descriptors)

    def query(self, query_graph, K=50, top=5):
        """
        Returns the label from the database using a query graph.
        """
        key = descriptor(query_graph, N=DESCRIPTOR_SIZE)

        # Query KD-tree
        dd, ii = self.kdtree.query(key, k=K)

        neighbors = []
        for i in ii:
            k = tuple(self.descriptors[i])

            features = self.bplustree.get(k)
            
            neighbors.append(features)


        return Counter(neighbors).most_common(top)
    
    def close(self):
        """
        Closes database.
        """
        self.bplustree.close()

    def insert(self, k, v):
        self.bplustree.insert(k, v)
    
    def checkpoint(self):
        self.bplustree.checkpoint()
    


def open_database(N=DESCRIPTOR_SIZE, value_size=250, filename=DATABASE_FILENAME) -> BPlusTree:
    """
    Create db, with key_size of 8 bytes (C double) times vector size, 
    Other parameters to be determined
    """
    db = NeighborBPlusTree(filename, 
                       serializer=VectorSerializer(), 
                       order=64, 
                       page_size=128*(8*N)*(8*value_size),
                       key_size=8*N)
    
    return Database(db)

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

def serialize_features(graph) -> bytes:
    """
    Converts graph features to a binary format that can be used later.
    
    Default implementation is to encode the label string.
    
    Instead, one can binarize vertorized features (look at encode graph matching function).
    """
    return graph.graph['label'].encode() 

def construct_database(iterator, N=DESCRIPTOR_SIZE, value_size=250, filename=DATABASE_FILENAME, serialize=serialize_features) -> BPlusTree:
    """
    Populates database with all graphs extracted from images, along with image index and label.
    
    Uses the algorithms described in Fonseca and Jorge "Indexing High-Dimensional Data for 
    Content-Based Retrieval in Large Databases".
    
    Constructs a B+tree that uses the index described in the paper to map labels, facilitates
    range queries and KNN queries. 
    
    The B+-tree maps the index to graph information, serialized to bytes.
    
    TO-DO: change from only encoding label to more graph features!
    """
    # Delete existing database
    erase_database(filename)
    
    # Create database
    db = NeighborBPlusTree(filename, 
            serializer=VectorSerializer(), 
            order=64, 
            page_size=128*(8*N)*(8*value_size),
            key_size=8*N)
    
    try:
        # Insert all key/value pairs into the database
        db.batch_insert(iterator)

        # Flush
        db.checkpoint()
        
        return Database(db) 
        
    except:
        # DB unexpected error, close.
        db.close()

        erase_database(filename)
        raise 

def erase_database(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

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

"""
------------------------------
-- Database implementation 
-- (BPlusTree module)
------------------------------
"""

class NeighborBPlusTree(BPlusTree): 
    """
    A BPlusTree that supports range and neighbor queries.
    """

    def get_neighbors(self, key, default={}) -> dict:
        with self._mem.read_transaction:
            node = self._search_in_tree(key, self._root_node)
            records = node.entries
            rv = {r.key: self._get_value_from_record(r) for r in records}
            assert isinstance(rv, dict)
            return rv
    
    def get_range(self, k_min, k_max, step=0.001, default={}) -> dict:
        with self._mem.read_transaction:
            all_records = []
            k = k_min
            while k <= k_max:
                node = self._search_in_tree(k, self._root_node)
                records = node.entries
                
                assert isinstance(node, (Node))
                
                all_records += records
                
                k = node.biggest_key + step
                            
            rv = {r.key: self._get_value_from_record(r) for r in all_records}
            
            assert isinstance(rv, dict)
            return rv
    
class VectorSerializer(Serializer):
    """
    A serializer for vectors of 8 byte doubles.
    """
    __slots__ = []
    
    def serialize(self, obj: tuple, key_size: int) -> bytes:
        return bytes(np.array(obj))

    def deserialize(self, data: bytes) -> tuple:
        return tuple(np.frombuffer(data, dtype=float))

"""
===========================
    DEPRECATED!!!
===========================
"""

def index(graph):
    """
    ===========================
        DEPRECATED!!!
    ===========================
    
    Get the index of the graph, as described in in Fonseca and Jorge 
    "Indexing High-Dimensional Data for Content-Based Retrieval in Large Databases".
    
    Is the norm of the topology descriptor.
    
    This is used as the index of a B+-tree to find graphs with similar topology.
    """
    # Compute topology descriptor
    d = descriptor(graph)
    
    # Get norm of eigenvalues (the reduction to 1 dimensions)
    norm = linalg.norm(d)
    
    return norm

def perturbe(index):
    """
    Add small random perturbation to avoid collisions
    """   
    epsilon = (2*random.random() - 1) / 100_000_000_000
    return index + epsilon
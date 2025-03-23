import os
import json
import pickle
from collections import defaultdict
import shutil
import threading

class IndexStorage:
    """
    Handles persistent storage of index data on disk.
    Provides methods for saving and loading different components of the search index.
    """
    def __init__(self, index_dir='index_data'):
        self.index_dir = index_dir
        self.document_dir = os.path.join(index_dir, 'documents')
        self.index_file = os.path.join(index_dir, 'inverted_index.pkl')
        self.term_doc_freq_file = os.path.join(index_dir, 'term_document_freq.pkl')
        self.metadata_file = os.path.join(index_dir, 'metadata.json')
        
        self._lock = threading.RLock()  # Thread-safe operations
        
        # Create necessary directories
        self._ensure_directories_exist()
    
    def _ensure_directories_exist(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.document_dir, exist_ok=True)
    
    def save_document(self, doc_id, document_data):
        """Save a document to disk"""
        with self._lock:
            doc_path = os.path.join(self.document_dir, f"{doc_id}.json")
            with open(doc_path, 'w') as f:
                json.dump(document_data, f)
    
    def load_document(self, doc_id):
        """Load a document from disk"""
        with self._lock:
            doc_path = os.path.join(self.document_dir, f"{doc_id}.json")
            if os.path.exists(doc_path):
                with open(doc_path, 'r') as f:
                    return json.load(f)
            return None
    
    def load_all_documents(self):
        """Load all documents from disk"""
        documents = {}
        with self._lock:
            if os.path.exists(self.document_dir):
                for filename in os.listdir(self.document_dir):
                    if filename.endswith('.json'):
                        doc_id = filename[:-5]  # Remove .json extension
                        doc_path = os.path.join(self.document_dir, filename)
                        with open(doc_path, 'r') as f:
                            documents[doc_id] = json.load(f)
        return documents
    
    def save_inverted_index(self, inverted_index):
        """Save inverted index to disk"""
        with self._lock:
            with open(self.index_file, 'wb') as f:
                pickle.dump(dict(inverted_index), f)
    
    def load_inverted_index(self):
        """Load inverted index from disk"""
        with self._lock:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'rb') as f:
                    return defaultdict(dict, pickle.load(f))
            return defaultdict(dict)
    
    def save_term_document_freq(self, term_document_freq):
        """Save term document frequency to disk"""
        with self._lock:
            with open(self.term_doc_freq_file, 'wb') as f:
                pickle.dump(dict(term_document_freq), f)
    
    def load_term_document_freq(self):
        """Load term document frequency from disk"""
        with self._lock:
            if os.path.exists(self.term_doc_freq_file):
                with open(self.term_doc_freq_file, 'rb') as f:
                    return defaultdict(int, pickle.load(f))
            return defaultdict(int)
    
    def save_metadata(self, metadata):
        """Save metadata to disk"""
        with self._lock:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f)
    
    def load_metadata(self):
        """Load metadata from disk"""
        with self._lock:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            return {'total_documents': 0}
    
    def clear_index(self):
        """Clear all index data"""
        with self._lock:
            if os.path.exists(self.index_dir):
                shutil.rmtree(self.index_dir)
            self._ensure_directories_exist()
    
    def get_index_size(self):
        """Get the total size of the index in bytes"""
        total_size = 0
        with self._lock:
            for dirpath, dirnames, filenames in os.walk(self.index_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
        return total_size
import re
from collections import defaultdict, Counter
import math
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from .storage import IndexStorage

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

class Indexer:
    def __init__(self, index_dir='index_data'):
        self.storage = IndexStorage(index_dir)
        self.inverted_index = defaultdict(dict)
        self.document_store = {}
        self.term_document_freq = defaultdict(int)
        self.total_documents = 0
        self.phrase_cache = {}
        
        # Load existing index if available
        self._load_index()
    
    def _preprocess_text(self, text):
        """Preprocess text: lowercase, remove punctuation, tokenize, remove stopwords"""
        if not text:
            return []
        
        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = re.sub(f'[{string.punctuation}]', ' ', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words and len(token) > 1]
        
        return tokens
    
    def _calculate_tf(self, term_freq, total_terms):
        """Calculate Term Frequency"""
        return term_freq / total_terms if total_terms > 0 else 0
    
    def _calculate_idf(self, term):
        """Calculate Inverse Document Frequency"""
        if term not in self.term_document_freq or self.total_documents == 0:
            return 0
        return math.log(self.total_documents / self.term_document_freq[term])
    
    def _build_document_vector(self, tokens):
        """Build document vector with term frequencies"""
        term_counts = Counter(tokens)
        total_terms = len(tokens)
        
        # Calculate TF for each term in the document
        document_vector = {}
        for term, count in term_counts.items():
            document_vector[term] = self._calculate_tf(count, total_terms)
            
        return document_vector
    
    def index_document(self, document):
        """Index a document and update the inverted index"""
        doc_id = document['id']
        title_tokens = self._preprocess_text(document.get('title', ''))
        data_tokens = self._preprocess_text(document.get('data', ''))
        
        # Create document record with tokens
        doc_record = {
            'id': doc_id,
            'title': document.get('title', ''),
            'data': document.get('data', ''),
            'title_tokens': title_tokens,
            'data_tokens': data_tokens
        }
        
        # Store document content
        self.document_store[doc_id] = doc_record
        
        # Save document to storage
        self.storage.save_document(doc_id, doc_record)
        
        # Build term vectors for title and data
        title_vector = self._build_document_vector(title_tokens)
        data_vector = self._build_document_vector(data_tokens)
        
        # Update inverted index
        updated_terms = set()
        
        # Index title terms
        for term, tf in title_vector.items():
            self.inverted_index[term][doc_id] = {
                'title_tf': tf,
                'data_tf': 0.0
            }
            updated_terms.add(term)
        
        # Index data terms
        for term, tf in data_vector.items():
            if term in self.inverted_index and doc_id in self.inverted_index[term]:
                self.inverted_index[term][doc_id]['data_tf'] = tf
            else:
                self.inverted_index[term][doc_id] = {
                    'title_tf': 0.0,
                    'data_tf': tf
                }
            updated_terms.add(term)
        
        # Update document frequency for each term
        for term in updated_terms:
            self.term_document_freq[term] += 1
        
        # Increment total document count
        self.total_documents += 1
        
        # Clear phrase cache as index has changed
        self.phrase_cache = {}
        
        # Save index to disk
        self._save_index()
        
        return True
    
    def _save_index(self):
        """Save inverted index and related data to disk"""
        # Save inverted index
        self.storage.save_inverted_index(self.inverted_index)
        
        # Save term document frequency
        self.storage.save_term_document_freq(self.term_document_freq)
        
        # Save document count
        self.storage.save_metadata({'total_documents': self.total_documents})
    
    def _load_index(self):
        """Load inverted index and related data from disk"""
        try:
            # Load inverted index
            self.inverted_index = self.storage.load_inverted_index()
            
            # Load document store
            self.document_store = self.storage.load_all_documents()
            
            # Load term document frequency
            self.term_document_freq = self.storage.load_term_document_freq()
            
            # Load document count
            metadata = self.storage.load_metadata()
            self.total_documents = metadata.get('total_documents', 0)
                    
        except Exception as e:
            print(f"Error loading index: {e}")
            # Initialize fresh index if loading fails
            self.inverted_index = defaultdict(dict)
            self.document_store = {}
            self.term_document_freq = defaultdict(int)
            self.total_documents = 0
    
    def get_index_stats(self):
        """Get statistics about the index"""
        return {
            'total_documents': self.total_documents,
            'unique_terms': len(self.inverted_index),
            'index_size_bytes': self.storage.get_index_size()
        }
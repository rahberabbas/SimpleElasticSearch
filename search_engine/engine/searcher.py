# search/engine/searcher.py
import re
from collections import defaultdict
import math

class Searcher:
    def __init__(self, indexer):
        self.indexer = indexer
    
    def _get_terms(self, query):
        """Process query and return list of terms"""
        return self.indexer._preprocess_text(query)
    
    def _detect_phrases(self, query):
        """Detect phrases in a query (surrounded by quotes)"""
        phrases = re.findall(r'"([^"]*)"', query)
        
        # Remove phrases from query to get remaining terms
        remaining_text = query
        for phrase in phrases:
            remaining_text = remaining_text.replace(f'"{phrase}"', '')
        
        # Get individual terms from remaining text
        individual_terms = self.indexer._preprocess_text(remaining_text)
        
        # Preprocess phrases
        processed_phrases = [self.indexer._preprocess_text(phrase) for phrase in phrases]
        
        return individual_terms, processed_phrases
    
    def search(self, query, field=None, use_phrase_query=False):
        """
        Search for documents matching the query
        
        Args:
            query (str): Search query
            field (str, optional): Specific field to search ('title' or 'data')
            use_phrase_query (bool): Whether to treat this as a phrase query
            
        Returns:
            list: List of matching documents, ranked by relevance
        """
        if not query:
            return []
        
        if use_phrase_query:
            return self._phrase_search(query, field)
        
        # Check phrase cache for exact query
        cache_key = f"{query}:{field}"
        if cache_key in self.indexer.phrase_cache:
            return self.indexer.phrase_cache[cache_key]
        
        # Detect phrases in query
        individual_terms, phrases = self._detect_phrases(query)
        
        # If we have both phrases and individual terms, handle both
        if phrases and individual_terms:
            phrase_results = self._phrase_search(" ".join(phrases[0]), field)
            term_results = self._term_search(individual_terms, field)
            
            # Merge results, keeping only documents that appear in both
            result_docs = {}
            
            # Start with documents from term search
            for doc in term_results:
                result_docs[doc['id']] = doc
            
            # Keep only documents that also appear in phrase results
            phrase_doc_ids = [doc['id'] for doc in phrase_results]
            for doc_id in list(result_docs.keys()):
                if doc_id not in phrase_doc_ids:
                    del result_docs[doc_id]
            
            return list(result_docs.values())
        
        # If we just have phrases
        elif phrases:
            results = self._phrase_search(" ".join(phrases[0]), field)
            return results
        
        # If we just have individual terms
        else:
            results = self._term_search(individual_terms, field)
            return results
    
    def _term_search(self, terms, field=None):
        """Search for documents containing the specified terms"""
        if not terms:
            return []
        
        # Calculate document scores
        doc_scores = defaultdict(float)
        
        for term in terms:
            if term not in self.indexer.inverted_index:
                continue
            
            # Calculate IDF for this term
            idf = self.indexer._calculate_idf(term)
            
            # For each document containing this term
            for doc_id, term_data in self.indexer.inverted_index[term].items():
                # If field is specified, only consider that field
                if field == 'title':
                    tf = term_data['title_tf']
                elif field == 'data':
                    tf = term_data['data_tf']
                else:
                    # Use the maximum TF from title or data
                    tf = max(term_data['title_tf'], term_data['data_tf'])
                
                # Calculate TF-IDF score
                doc_scores[doc_id] += tf * idf
        
        # Sort documents by score
        ranked_docs = [(doc_id, score) for doc_id, score in doc_scores.items()]
        ranked_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Retrieve document data
        results = []
        for doc_id, score in ranked_docs:
            if doc_id in self.indexer.document_store:
                doc = self.indexer.document_store[doc_id]
                results.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'data': doc['data'],
                    'score': score
                })
        
        return results
    
    def _phrase_search(self, phrase, field=None):
        """Search for documents containing the exact phrase"""
        # Check cache first
        cache_key = f"{phrase}:{field}"
        if cache_key in self.indexer.phrase_cache:
            return self.indexer.phrase_cache[cache_key]
        
        # Process phrase into terms
        phrase_terms = self.indexer._preprocess_text(phrase)
        
        if not phrase_terms:
            return []
        
        # Find documents containing all terms in the phrase
        candidate_docs = set()
        
        # Start with documents containing the first term
        if phrase_terms[0] in self.indexer.inverted_index:
            candidate_docs = set(self.indexer.inverted_index[phrase_terms[0]].keys())
        else:
            return []  # First term not found, no matches
        
        # Filter to documents containing all terms
        for term in phrase_terms[1:]:
            if term not in self.indexer.inverted_index:
                return []  # One of the terms not found, no matches
            
            term_docs = set(self.indexer.inverted_index[term].keys())
            candidate_docs &= term_docs
        
        # Now we need to verify that the terms appear consecutively in the documents
        results = []
        
        for doc_id in candidate_docs:
            doc = self.indexer.document_store[doc_id]
            
            # Check if phrase exists in title or data based on field parameter
            phrase_in_title = False
            phrase_in_data = False
            
            if field is None or field == 'title':
                title_tokens = doc['title_tokens']
                if self._check_consecutive_terms(title_tokens, phrase_terms):
                    phrase_in_title = True
            
            if field is None or field == 'data':
                data_tokens = doc['data_tokens']
                if self._check_consecutive_terms(data_tokens, phrase_terms):
                    phrase_in_data = True
            
            if phrase_in_title or phrase_in_data:
                score = 0.0
                
                # Calculate score based on term frequencies and IDF
                for term in phrase_terms:
                    if term in self.indexer.inverted_index and doc_id in self.indexer.inverted_index[term]:
                        term_data = self.indexer.inverted_index[term][doc_id]
                        
                        if field == 'title':
                            tf = term_data['title_tf']
                        elif field == 'data':
                            tf = term_data['data_tf']
                        else:
                            tf = max(term_data['title_tf'], term_data['data_tf'])
                        
                        idf = self.indexer._calculate_idf(term)
                        score += tf * idf
                
                # Boost score for phrase match
                score *= 2.0
                
                results.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'data': doc['data'],
                    'score': score
                })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Cache results
        self.indexer.phrase_cache[cache_key] = results
        
        return results
    
    def _check_consecutive_terms(self, tokens, phrase_terms):
        """Check if phrase terms appear consecutively in tokens"""
        if len(tokens) < len(phrase_terms):
            return False
        
        for i in range(len(tokens) - len(phrase_terms) + 1):
            match = True
            for j in range(len(phrase_terms)):
                if tokens[i + j] != phrase_terms[j]:
                    match = False
                    break
            
            if match:
                return True
        
        return False
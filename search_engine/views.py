from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404

from .models import Document
from .serializers import DocumentSerializer
from .engine.indexer import Indexer
from .engine.searcher import Searcher

# Create global instances of indexer and searcher
indexer = Indexer()
searcher = Searcher(indexer)

class IndexView(APIView):
    """
    API endpoint for indexing documents
    """
    def post(self, request, format=None):
        serializer = DocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            # Extract the data from serializer
            doc_data = {
                'id': request.data.get('id'),  # Get ID directly from request.data
                'title': serializer.validated_data.get('title', ''),
                'data': serializer.validated_data.get('data', '')
            }
            
            # Save to database
            document, created = Document.objects.update_or_create(
                document_id=doc_data['id'],
                defaults={
                    'title': doc_data.get('title', ''),
                    'data': doc_data.get('data', '')
                }
            )
            
            # Index the document
            indexer.index_document(doc_data)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchView(APIView):
    """
    API endpoint for searching documents
    """
    def get(self, request, format=None):
        query = request.query_params.get('q', '')
        field = request.query_params.get('field', None)
        phrase_query = request.query_params.get('phrase', '').lower() == 'true'
        
        if not query:
            return Response([], status=status.HTTP_200_OK)
        
        # Perform search
        results = searcher.search(query, field=field, use_phrase_query=phrase_query)
        
        # Remove score from results
        for result in results:
            if 'score' in result:
                del result['score']
        
        return Response(results, status=status.HTTP_200_OK)
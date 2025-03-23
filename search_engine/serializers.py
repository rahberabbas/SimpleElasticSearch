from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    # Define id as a separate field that maps to document_id
    id = serializers.CharField(source='document_id')
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'data']
    
    def to_internal_value(self, data):
        # This ensures that the 'id' field from the request is properly
        # mapped to 'document_id' in the model
        internal_value = super().to_internal_value(data)
        return internal_value
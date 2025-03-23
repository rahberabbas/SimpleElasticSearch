from django.db import models

# Create your models here.
class Document(models.Model):
    """
    Model to keep track of indexed documents.
    
    Note: The actual document content and index are stored in the file system,
    this is just a reference for the API.
    """
    document_id = models.CharField(max_length=255, primary_key=True)
    title = models.TextField(blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents'
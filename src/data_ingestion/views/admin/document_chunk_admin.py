"""
Admin API Views for DocumentChunk Management

Admin-only endpoints for managing document chunks.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
from rest_framework import status
from rest_framework import serializers
from main_system.base.auth_api import AuthAPI
from main_system.permissions.admin_permission import AdminPermission
from main_system.views.admin.bulk_operation import BaseBulkOperationAPI
from main_system.views.admin.base import (
    BaseAdminDetailAPI,
    BaseAdminDeleteAPI,
)
from data_ingestion.services.document_chunk_service import DocumentChunkService
from data_ingestion.serializers.document_chunk.admin import (
    DocumentChunkAdminListQuerySerializer,
    BulkDocumentChunkOperationSerializer,
)


class DocumentChunkListSerializer(serializers.Serializer):
    """Serializer for document chunk list."""
    id = serializers.UUIDField()
    document_version_id = serializers.UUIDField()
    chunk_index = serializers.IntegerField()
    has_embedding = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class DocumentChunkDetailSerializer(serializers.Serializer):
    """Serializer for document chunk detail."""
    id = serializers.UUIDField()
    document_version_id = serializers.UUIDField()
    chunk_text = serializers.CharField()
    chunk_index = serializers.IntegerField()
    has_embedding = serializers.BooleanField()
    metadata = serializers.JSONField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class DocumentChunkAdminListAPI(AuthAPI):
    """
    Admin: Get list of all document chunks with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-chunks/
    Auth: Required (staff/superuser only)
    Query Params:
        - document_version_id: Filter by document version ID
        - has_embedding: Filter by embedding presence (true/false)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = DocumentChunkAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        chunks = DocumentChunkService.get_by_filters(
            document_version_id=str(query_serializer.validated_data.get('document_version_id')) if query_serializer.validated_data.get('document_version_id') else None,
            has_embedding=query_serializer.validated_data.get('has_embedding')
        )
        
        return self.api_response(
            message="Document chunks retrieved successfully.",
            data=[DocumentChunkListSerializer({
                'id': chunk.id,
                'document_version_id': chunk.document_version.id,
                'chunk_index': chunk.chunk_index,
                'has_embedding': chunk.embedding is not None,
                'created_at': chunk.created_at,
            }).data for chunk in chunks],
            status_code=status.HTTP_200_OK
        )


class DocumentChunkAdminDetailAPI(BaseAdminDetailAPI):
    """
    Admin: Get detailed document chunk information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-chunks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document chunk"
    
    def get_entity_by_id(self, entity_id):
        """Get document chunk by ID."""
        return DocumentChunkService.get_by_id(entity_id)
    
    def get_serializer_class(self):
        """Return the detail serializer."""
        return DocumentChunkDetailSerializer
    
    def get(self, request, id):
        """Override to use custom serializer with model instance."""
        chunk = self.get_entity_by_id(id)
        if not chunk:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DocumentChunkDetailSerializer({
            'id': chunk.id,
            'document_version_id': chunk.document_version.id,
            'chunk_text': chunk.chunk_text,
            'chunk_index': chunk.chunk_index,
            'has_embedding': chunk.embedding is not None,
            'metadata': chunk.metadata,
            'created_at': chunk.created_at,
            'updated_at': chunk.updated_at,
        })
        
        return self.api_response(
            message=f"{self.get_entity_name()} retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )


class DocumentChunkAdminDeleteAPI(BaseAdminDeleteAPI):
    """
    Admin: Delete document chunk.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/document-chunks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document chunk"
    
    def get_entity_by_id(self, entity_id):
        """Get document chunk by ID."""
        return DocumentChunkService.get_by_id(entity_id)
    
    def delete_entity(self, entity):
        """Delete the document chunk."""
        return DocumentChunkService.delete_document_chunk(str(entity.id))


class BulkDocumentChunkOperationAPI(BaseBulkOperationAPI):
    """
    Admin: Perform bulk operations on document chunks.
    
    Endpoint: POST /api/v1/data-ingestion/admin/document-chunks/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [AdminPermission]
    
    def get_serializer_class(self):
        """Return the bulk document chunk operation serializer."""
        return BulkDocumentChunkOperationSerializer
    
    def get_entity_name(self):
        """Get human-readable entity name."""
        return "Document chunk"
    
    def get_entity_by_id(self, entity_id):
        """Get document chunk by ID."""
        return DocumentChunkService.get_by_id(entity_id)
    
    def execute_operation(self, entity, operation, validated_data):
        """Execute the operation on the document chunk."""
        if operation == 'delete':
            return DocumentChunkService.delete_document_chunk(str(entity.id))
        elif operation == 're_embed':
            # TODO: Implement re-embedding logic
            # This would require calling the embedding service
            raise ValueError('Re-embedding not yet implemented')
        else:
            raise ValueError(f"Invalid operation: {operation}")

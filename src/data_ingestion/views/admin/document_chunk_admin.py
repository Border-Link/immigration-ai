"""
Admin API Views for DocumentChunk Management

Admin-only endpoints for managing document chunks.
Access restricted to staff/superusers using IsAdminOrStaff permission.

Features:
- List document chunks with advanced filtering
- View detailed chunk information
- Delete chunks
- Bulk operations (delete, re-embed)
- Statistics and analytics
"""
import logging
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

logger = logging.getLogger('django')


class DocumentChunkListSerializer(serializers.Serializer):
    """Serializer for document chunk list with related data."""
    id = serializers.UUIDField()
    document_version_id = serializers.UUIDField()
    document_version_hash = serializers.CharField(required=False, allow_null=True)
    source_document_id = serializers.UUIDField(required=False, allow_null=True)
    source_url = serializers.CharField(required=False, allow_null=True)
    chunk_index = serializers.IntegerField()
    chunk_text_preview = serializers.CharField(required=False)
    chunk_text_length = serializers.IntegerField(required=False)
    has_embedding = serializers.BooleanField()
    metadata = serializers.JSONField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class DocumentChunkDetailSerializer(serializers.Serializer):
    """Serializer for document chunk detail with full related data."""
    id = serializers.UUIDField()
    document_version_id = serializers.UUIDField()
    document_version_hash = serializers.CharField(required=False, allow_null=True)
    document_version_extracted_at = serializers.DateTimeField(required=False, allow_null=True)
    source_document_id = serializers.UUIDField(required=False, allow_null=True)
    source_document_url = serializers.CharField(required=False, allow_null=True)
    source_document_fetched_at = serializers.DateTimeField(required=False, allow_null=True)
    chunk_text = serializers.CharField()
    chunk_index = serializers.IntegerField()
    has_embedding = serializers.BooleanField()
    embedding_dimensions = serializers.IntegerField(required=False, allow_null=True)
    metadata = serializers.JSONField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(allow_null=True)


class DocumentChunkAdminListAPI(AuthAPI):
    """
    Admin: Get list of all document chunks with advanced filtering and pagination.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-chunks/
    Auth: Required (staff/superuser only)
    
    Query Params:
        - document_version_id: Filter by document version ID (UUID)
        - has_embedding: Filter by embedding presence (true/false)
        - page: Page number for pagination (default: 1)
        - page_size: Items per page (default: 50, max: 200)
        - include_text_preview: Include text preview in response (default: false)
    """
    permission_classes = [AdminPermission]
    
    def get(self, request):
        query_serializer = DocumentChunkAdminListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        
        validated_data = query_serializer.validated_data
        
        # Get chunks with filters
        chunks = DocumentChunkService.get_by_filters(
            document_version_id=str(validated_data.get('document_version_id')) if validated_data.get('document_version_id') else None,
            has_embedding=validated_data.get('has_embedding')
        )
        
        # Pagination
        page = validated_data.get('page', 1)
        page_size = min(validated_data.get('page_size', 50), 200)  # Max 200 per page
        
        total_count = chunks.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        paginated_chunks = chunks[start_index:end_index]
        
        # Serialize with related data
        include_preview = validated_data.get('include_text_preview', False)
        serialized_data = []
        
        for chunk in paginated_chunks:
            chunk_data = {
                'id': chunk.id,
                'document_version_id': chunk.document_version.id,
                'document_version_hash': chunk.document_version.content_hash[:16] if chunk.document_version.content_hash else None,
                'source_document_id': chunk.document_version.source_document.id if chunk.document_version.source_document else None,
                'source_url': chunk.document_version.source_document.source_url if chunk.document_version.source_document else None,
                'chunk_index': chunk.chunk_index,
                'chunk_text_length': len(chunk.chunk_text),
                'has_embedding': chunk.embedding is not None,
                'metadata': chunk.metadata,
                'created_at': chunk.created_at,
                'updated_at': chunk.updated_at,
            }
            
            if include_preview:
                # Include first 200 characters as preview
                chunk_data['chunk_text_preview'] = chunk.chunk_text[:200] + ('...' if len(chunk.chunk_text) > 200 else '')
            
            serialized_data.append(DocumentChunkListSerializer(chunk_data).data)
        
        return self.api_response(
            message="Document chunks retrieved successfully.",
            data={
                'results': serialized_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0,
                    'has_next': end_index < total_count,
                    'has_previous': page > 1,
                }
            },
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
        """Override to use custom serializer with full related data."""
        chunk = self.get_entity_by_id(id)
        if not chunk:
            return self.api_response(
                message=f"{self.get_entity_name()} with ID '{id}' not found.",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Get related data
        doc_version = chunk.document_version
        source_doc = doc_version.source_document if doc_version else None
        
        serializer = DocumentChunkDetailSerializer({
            'id': chunk.id,
            'document_version_id': doc_version.id if doc_version else None,
            'document_version_hash': doc_version.content_hash if doc_version else None,
            'document_version_extracted_at': doc_version.extracted_at if doc_version else None,
            'source_document_id': source_doc.id if source_doc else None,
            'source_document_url': source_doc.source_url if source_doc else None,
            'source_document_fetched_at': source_doc.fetched_at if source_doc else None,
            'chunk_text': chunk.chunk_text,
            'chunk_index': chunk.chunk_index,
            'has_embedding': chunk.embedding is not None,
            'embedding_dimensions': len(chunk.embedding) if chunk.embedding is not None else None,
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
        """
        Execute the operation on the document chunk.
        
        Supported operations:
        - delete: Delete the chunk
        - re_embed: Regenerate embedding for the chunk
        """
        if operation == 'delete':
            return DocumentChunkService.delete_document_chunk(str(entity.id))
        elif operation == 're_embed':
            # Get model from validated_data if provided, otherwise use default
            model = validated_data.get('model', 'text-embedding-ada-002')
            return DocumentChunkService.regenerate_embedding(str(entity.id), model=model)
        else:
            raise ValueError(f"Invalid operation: {operation}. Supported operations: delete, re_embed")
    
    def get_success_data(self, entity, operation_result):
        """
        Get data to include in success results.
        
        Returns entity ID and operation-specific data.
        """
        return {
            'chunk_id': str(entity.id),
            'chunk_index': entity.chunk_index,
            'document_version_id': str(entity.document_version.id) if entity.document_version else None,
        }

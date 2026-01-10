"""
Admin API Views for DocumentChunk Management

Admin-only endpoints for managing document chunks.
Access restricted to staff/superusers using IsAdminOrStaff permission.
"""
import logging
from rest_framework import status
from main_system.base.auth_api import AuthAPI
from main_system.permissions.is_admin_or_staff import IsAdminOrStaff
from data_ingestion.services.document_chunk_service import DocumentChunkService
from data_ingestion.serializers.document_chunk.admin import BulkDocumentChunkOperationSerializer
from django.utils.dateparse import parse_datetime

logger = logging.getLogger('django')


class DocumentChunkListSerializer:
    """Simple serializer for document chunk list."""
    @staticmethod
    def to_dict(chunk):
        return {
            'id': str(chunk.id),
            'document_version_id': str(chunk.document_version.id),
            'chunk_index': chunk.chunk_index,
            'has_embedding': chunk.embedding is not None,
            'created_at': chunk.created_at.isoformat() if chunk.created_at else None,
        }


class DocumentChunkDetailSerializer:
    """Simple serializer for document chunk detail."""
    @staticmethod
    def to_dict(chunk):
        return {
            'id': str(chunk.id),
            'document_version_id': str(chunk.document_version.id),
            'chunk_text': chunk.chunk_text,
            'chunk_index': chunk.chunk_index,
            'has_embedding': chunk.embedding is not None,
            'metadata': chunk.metadata,
            'created_at': chunk.created_at.isoformat() if chunk.created_at else None,
            'updated_at': chunk.updated_at.isoformat() if chunk.updated_at else None,
        }


class DocumentChunkAdminListAPI(AuthAPI):
    """
    Admin: Get list of all document chunks with advanced filtering.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-chunks/
    Auth: Required (staff/superuser only)
    Query Params:
        - document_version_id: Filter by document version ID
        - has_embedding: Filter by embedding presence (true/false)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        document_version_id = request.query_params.get('document_version_id', None)
        has_embedding = request.query_params.get('has_embedding', None)
        
        try:
            # Parse parameters
            has_embedding_bool = has_embedding.lower() == 'true' if has_embedding is not None else None
            
            # Use service method with filters
            chunks = DocumentChunkService.get_by_filters(
                document_version_id=document_version_id,
                has_embedding=has_embedding_bool
            )
            
            return self.api_response(
                message="Document chunks retrieved successfully.",
                data=[DocumentChunkListSerializer.to_dict(chunk) for chunk in chunks],
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document chunks.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentChunkAdminDetailAPI(AuthAPI):
    """
    Admin: Get detailed document chunk information.
    
    Endpoint: GET /api/v1/data-ingestion/admin/document-chunks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request, id):
        try:
            chunk = DocumentChunkService.get_by_id(id)
            if not chunk:
                return self.api_response(
                    message=f"Document chunk with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            return self.api_response(
                message="Document chunk retrieved successfully.",
                data=DocumentChunkDetailSerializer.to_dict(chunk),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error retrieving document chunk {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error retrieving document chunk.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentChunkAdminDeleteAPI(AuthAPI):
    """
    Admin: Delete document chunk.
    
    Endpoint: DELETE /api/v1/data-ingestion/admin/document-chunks/<id>/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def delete(self, request, id):
        try:
            deleted = DocumentChunkService.delete_document_chunk(id)
            if not deleted:
                return self.api_response(
                    message=f"Document chunk with ID '{id}' not found.",
                    data=None,
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            return self.api_response(
                message="Document chunk deleted successfully.",
                data=None,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deleting document chunk {id}: {e}", exc_info=True)
            return self.api_response(
                message="Error deleting document chunk.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkDocumentChunkOperationAPI(AuthAPI):
    """
    Admin: Perform bulk operations on document chunks.
    
    Endpoint: POST /api/v1/data-ingestion/admin/document-chunks/bulk-operation/
    Auth: Required (staff/superuser only)
    """
    permission_classes = [IsAdminOrStaff]
    
    def post(self, request):
        serializer = BulkDocumentChunkOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        chunk_ids = serializer.validated_data['chunk_ids']
        operation = serializer.validated_data['operation']
        
        results = {
            'success': [],
            'failed': []
        }
        
        try:
            for chunk_id in chunk_ids:
                try:
                    if operation == 'delete':
                        deleted = DocumentChunkService.delete_document_chunk(str(chunk_id))
                        if deleted:
                            results['success'].append(str(chunk_id))
                        else:
                            results['failed'].append({
                                'chunk_id': str(chunk_id),
                                'error': 'Document chunk not found or failed to delete'
                            })
                    elif operation == 're_embed':
                        # TODO: Implement re-embedding logic
                        # This would require calling the embedding service
                        results['failed'].append({
                            'chunk_id': str(chunk_id),
                            'error': 'Re-embedding not yet implemented'
                        })
                except Exception as e:
                    results['failed'].append({
                        'chunk_id': str(chunk_id),
                        'error': str(e)
                    })
            
            return self.api_response(
                message=f"Bulk operation '{operation}' completed. {len(results['success'])} succeeded, {len(results['failed'])} failed.",
                data=results,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error in bulk operation: {e}", exc_info=True)
            return self.api_response(
                message="Error performing bulk operation.",
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

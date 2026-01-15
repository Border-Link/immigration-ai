"""
API tests for admin document chunk endpoints.
"""

import pytest
from rest_framework import status
from unittest.mock import patch


API_PREFIX = "/api/v1/data-ingestion"


@pytest.mark.django_db
class TestAdminDocumentChunkViews:
    def test_list_success_with_pagination_and_preview(self, api_client, staff_user, document_chunks, document_version):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(
            f"{API_PREFIX}/admin/document-chunks/?document_version_id={document_version.id}&include_text_preview=true&page=1&page_size=1"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "results" in resp.data["data"]
        assert resp.data["data"]["pagination"]["page_size"] == 1
        assert len(resp.data["data"]["results"]) == 1
        assert "chunk_text_preview" in resp.data["data"]["results"][0]

    def test_detail_success(self, api_client, staff_user, document_chunks):
        api_client.force_authenticate(user=staff_user)
        chunk = document_chunks[0]
        resp = api_client.get(f"{API_PREFIX}/admin/document-chunks/{chunk.id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["data"]["id"] == str(chunk.id)
        assert "chunk_text" in resp.data["data"]

    def test_delete_success(self, api_client, staff_user, document_chunks):
        api_client.force_authenticate(user=staff_user)
        chunk = document_chunks[0]
        resp = api_client.delete(f"{API_PREFIX}/admin/document-chunks/{chunk.id}/delete/")
        assert resp.status_code == status.HTTP_200_OK

    @patch("data_ingestion.services.document_chunk_service.DocumentChunkService.regenerate_embedding", return_value=True)
    def test_bulk_re_embed_success(self, _mock_reembed, api_client, staff_user, document_chunks):
        api_client.force_authenticate(user=staff_user)
        chunk = document_chunks[0]
        resp = api_client.post(
            f"{API_PREFIX}/admin/document-chunks/bulk-operation/",
            {"operation": "re_embed", "chunk_ids": [str(chunk.id)], "model": "test-model"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["data"]["success"]) == 1


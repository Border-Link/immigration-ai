import json
from unittest.mock import MagicMock

import pytest

from data_ingestion.ingestion.uk_ingestion import UKIngestionSystem


class TestUKIngestionSystem:
    def test_extract_text_json_success(self):
        ds = MagicMock(jurisdiction="UK", base_url="https://www.gov.uk/api/content/entering-staying-uk")
        system = UKIngestionSystem(ds)
        raw = json.dumps(
            {
                "title": "T",
                "description": "D",
                "base_path": "/x",
                "web_url": "https://www.gov.uk/x",
                "content_id": "cid",
                "document_type": "taxon",
                "schema_name": "schema",
                "first_published_at": "2020-01-01",
                "public_updated_at": "2020-01-02",
                "phase": "live",
                "locale": "en",
                "details": {"internal_name": "n"},
                "links": {
                    "child_taxons": [{"title": "Child", "api_url": "https://www.gov.uk/api/content/child"}],
                    "parent_taxons": [{"title": "Parent", "api_url": "https://www.gov.uk/api/content/parent"}],
                },
            }
        )
        text = system.extract_text(raw, "application/json")
        assert "Title: T" in text
        assert "Child Taxons" in text

    def test_extract_text_invalid_json_returns_raw(self):
        ds = MagicMock(jurisdiction="UK", base_url="https://www.gov.uk/api/content/entering-staying-uk")
        system = UKIngestionSystem(ds)
        raw = "{not-json"
        text = system.extract_text(raw, "application/json")
        assert text == raw

    def test_extract_metadata_success(self):
        ds = MagicMock(jurisdiction="UK", base_url="https://www.gov.uk/api/content/entering-staying-uk")
        system = UKIngestionSystem(ds)
        raw = json.dumps({"content_id": "cid", "base_path": "/x", "links": {"child_taxons": [{"content_id": "c1", "api_url": "u1"}]}})
        meta = system.extract_metadata(raw)
        assert meta["content_id"] == "cid"
        assert "links" in meta

    def test_parse_api_response_filters_withdrawn(self):
        ds = MagicMock(jurisdiction="UK", base_url="https://www.gov.uk/api/content/entering-staying-uk")
        system = UKIngestionSystem(ds)
        response = {"links": {"child_taxons": [{"api_url": "u1", "withdrawn": False}, {"api_url": "u2", "withdrawn": True}]}}
        urls = system.parse_api_response(response)
        assert urls == ["u1"]


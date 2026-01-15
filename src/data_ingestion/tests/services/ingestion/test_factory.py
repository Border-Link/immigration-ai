from unittest.mock import MagicMock

from data_ingestion.ingestion.factory import IngestionSystemFactory
from data_ingestion.ingestion.base_ingestion import BaseIngestionSystem


class DummySystem(BaseIngestionSystem):
    def fetch_content(self, url: str):
        return {"content": "x", "content_type": "text/plain", "status_code": 200}

    def extract_text(self, raw_content: str, content_type: str) -> str:
        return raw_content

    def parse_api_response(self, response):
        return []

    def get_document_urls(self):
        return []


class TestIngestionSystemFactory:
    def test_get_supported_jurisdictions_contains_uk(self):
        assert "UK" in IngestionSystemFactory.get_supported_jurisdictions()

    def test_create_unsupported_returns_none(self):
        ds = MagicMock(jurisdiction="XX")
        assert IngestionSystemFactory.create(ds) is None

    def test_register_system_and_create(self):
        ds = MagicMock(jurisdiction="ZZ")
        IngestionSystemFactory.register_system("ZZ", DummySystem)
        system = IngestionSystemFactory.create(ds)
        assert isinstance(system, DummySystem)


import uuid

import pytest


@pytest.mark.django_db
class TestAICitationService:
    def test_create_and_get_by_id(self, ai_citation_service, reasoning_log, document_version):
        citation = ai_citation_service.create_citation(
            reasoning_log_id=str(reasoning_log.id),
            document_version_id=str(document_version.id),
            excerpt="Excerpt",
            relevance_score=0.75,
        )
        assert citation is not None

        fetched = ai_citation_service.get_by_id(str(citation.id))
        assert fetched is not None
        assert str(fetched.id) == str(citation.id)

    def test_get_by_id_not_found(self, ai_citation_service):
        assert ai_citation_service.get_by_id(str(uuid.uuid4())) is None

    def test_get_by_reasoning_log(self, ai_citation_service, citation, reasoning_log):
        citations = ai_citation_service.get_by_reasoning_log(str(reasoning_log.id))
        assert citations.count() >= 1

    def test_get_by_document_version(self, ai_citation_service, citation, document_version):
        citations = ai_citation_service.get_by_document_version(str(document_version.id))
        assert citations.count() >= 1

    def test_update_citation(self, ai_citation_service, citation):
        updated = ai_citation_service.update_citation(str(citation.id), relevance_score=0.95)
        assert updated is not None
        assert float(updated.relevance_score) == pytest.approx(0.95)

    def test_delete_citation(self, ai_citation_service, citation):
        assert ai_citation_service.delete_citation(str(citation.id)) is True
        assert ai_citation_service.get_by_id(str(citation.id)) is None

    def test_get_by_filters(self, ai_citation_service, citation, reasoning_log):
        citations = ai_citation_service.get_by_filters(reasoning_log_id=str(reasoning_log.id), min_relevance=0.5)
        assert citations.count() >= 1

    def test_get_by_quality_filters(self, ai_citation_service, citation):
        all_citations = ai_citation_service.get_all()
        buckets = ai_citation_service.get_by_quality_filters(all_citations, min_relevance=0.0)
        assert set(buckets.keys()) == {"all", "high_quality", "medium_quality", "low_quality"}
        assert buckets["all"].count() >= 1

    def test_get_statistics_returns_dict(self, ai_citation_service, citation):
        stats = ai_citation_service.get_statistics()
        assert isinstance(stats, dict)


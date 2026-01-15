from data_ingestion.helpers.metrics import (
    track_document_ingestion,
    track_document_parsing,
    track_document_chunking,
    track_batch_processing,
)


class TestMetrics:
    def test_metrics_helpers_do_not_raise(self):
        track_document_ingestion(source_type="gov_uk", status="success", duration=0.1, size_bytes=100)
        track_document_parsing(
            status="success",
            jurisdiction="UK",
            duration=0.2,
            rules_created=1,
            tokens_prompt=10,
            tokens_completion=5,
            cost_usd=0.01,
        )
        track_document_chunking(chunking_strategy="fixed_size", duration=0.1, chunks_count=2)
        track_batch_processing(status="success", duration=0.5, items_processed=3)


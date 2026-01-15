from data_ingestion.helpers.parallel_processor import ParallelProcessor, StreamingProcessor


class TestParallelProcessor:
    def test_process_in_parallel_success(self):
        items = [1, 2, 3]

        def f(x):
            return x * 2

        results = ParallelProcessor.process_in_parallel(items, f, max_workers=2)
        assert len(results) == 3
        assert all(r["success"] for r in results)

    def test_process_in_parallel_continue_on_error_false(self):
        items = [1, 2, 3]

        def f(x):
            if x == 2:
                raise ValueError("bad")
            return x

        results = ParallelProcessor.process_in_parallel(items, f, max_workers=2, continue_on_error=False)
        assert any(r["success"] is False for r in results)


class TestStreamingProcessor:
    def test_process_in_chunks_basic(self):
        text = "abcdefghij"
        chunks = StreamingProcessor.process_in_chunks(text=text, chunk_size=4, overlap=1, process_chunk_func=lambda c: {"chunk": c})
        assert len(chunks) >= 2
        assert chunks[0]["chunk"] == "abcd"

    def test_merge_chunk_results_deduplicates(self):
        merged = StreamingProcessor.merge_chunk_results(
            [
                {"rules": [{"requirement_code": "A", "description": "x"}], "tokens_used": 1, "estimated_cost": 0.1},
                {"rules": [{"requirement_code": "A", "description": "x"}], "tokens_used": 2, "estimated_cost": 0.2},
            ]
        )
        assert merged["unique_rules_count"] == 1
        assert merged["tokens_used"] == 3
        assert merged["estimated_cost"] == 0.3


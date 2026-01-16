"""
Unit tests for transcript archive tasks.
"""

from unittest.mock import MagicMock


class TestTranscriptArchiveTasks:
    def test_archive_old_transcripts_archives_each_and_returns_count(self, monkeypatch):
        from ai_calls.tasks.transcript_archive_tasks import archive_old_transcripts_task
        from ai_calls.tasks import transcript_archive_tasks as task_module

        t1 = MagicMock(id="t1")
        t2 = MagicMock(id="t2")

        monkeypatch.setattr(task_module.CallTranscriptSelector, "get_hot_storage_transcripts", MagicMock(return_value=[t1, t2]))
        monkeypatch.setattr(task_module.CallTranscriptRepository, "archive_transcript", MagicMock())

        res = archive_old_transcripts_task.run(days_threshold=90)
        assert res == 2
        assert task_module.CallTranscriptRepository.archive_transcript.call_count == 2

    def test_archive_old_transcripts_continues_on_per_item_failure(self, monkeypatch):
        from ai_calls.tasks.transcript_archive_tasks import archive_old_transcripts_task
        from ai_calls.tasks import transcript_archive_tasks as task_module

        t1 = MagicMock(id="t1")
        t2 = MagicMock(id="t2")

        monkeypatch.setattr(task_module.CallTranscriptSelector, "get_hot_storage_transcripts", MagicMock(return_value=[t1, t2]))

        def _archive_side_effect(t):
            if t.id == "t1":
                raise Exception("boom")
            return True

        monkeypatch.setattr(task_module.CallTranscriptRepository, "archive_transcript", MagicMock(side_effect=_archive_side_effect))

        res = archive_old_transcripts_task.run(days_threshold=90)
        assert res == 1

    def test_archive_old_transcripts_returns_zero_on_selector_failure(self, monkeypatch):
        from ai_calls.tasks.transcript_archive_tasks import archive_old_transcripts_task
        from ai_calls.tasks import transcript_archive_tasks as task_module

        monkeypatch.setattr(task_module.CallTranscriptSelector, "get_hot_storage_transcripts", MagicMock(side_effect=Exception("boom")))
        res = archive_old_transcripts_task.run(days_threshold=90)
        assert res == 0


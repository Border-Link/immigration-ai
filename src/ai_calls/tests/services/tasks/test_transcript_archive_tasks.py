"""
Unit tests for transcript archive tasks.
"""

from unittest.mock import MagicMock


class TestTranscriptArchiveTasks:
    def test_archive_old_transcripts_archives_each_and_returns_count(self, monkeypatch):
        from ai_calls.tasks.transcript_archive_tasks import archive_old_transcripts_task
        from ai_calls.tasks import transcript_archive_tasks as task_module

        monkeypatch.setattr(task_module.TranscriptArchiveService, "archive_old_transcripts", MagicMock(return_value=2))

        res = archive_old_transcripts_task.run(days_threshold=90)
        assert res == 2
        task_module.TranscriptArchiveService.archive_old_transcripts.assert_called_once()

    def test_archive_old_transcripts_continues_on_per_item_failure(self, monkeypatch):
        from ai_calls.tasks.transcript_archive_tasks import archive_old_transcripts_task
        from ai_calls.tasks import transcript_archive_tasks as task_module

        # Simulate service archiving 1 out of 2 items.
        monkeypatch.setattr(task_module.TranscriptArchiveService, "archive_old_transcripts", MagicMock(return_value=1))

        res = archive_old_transcripts_task.run(days_threshold=90)
        assert res == 1

    def test_archive_old_transcripts_returns_zero_on_selector_failure(self, monkeypatch):
        from ai_calls.tasks.transcript_archive_tasks import archive_old_transcripts_task
        from ai_calls.tasks import transcript_archive_tasks as task_module

        monkeypatch.setattr(task_module.TranscriptArchiveService, "archive_old_transcripts", MagicMock(side_effect=Exception("boom")))
        res = archive_old_transcripts_task.run(days_threshold=90)
        assert res == 0


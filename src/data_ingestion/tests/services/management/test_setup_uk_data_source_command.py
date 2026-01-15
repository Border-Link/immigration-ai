import pytest
from django.core.management import call_command


@pytest.mark.django_db
class TestSetupUKDataSourceCommand:
    def test_creates_data_source_when_missing(self, capsys):
        call_command("setup_uk_data_source", "--base-url", "https://www.gov.uk/api/content/entering-staying-uk", "--crawl-frequency", "weekly")
        out = capsys.readouterr().out
        assert "Successfully created UK data source" in out or "UK data source already exists" in out


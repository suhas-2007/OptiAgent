import pytest


@pytest.fixture(autouse=True)
def offline_test_environment(monkeypatch):
    """Regression runs must never consume a real Gemini key or paid API quota."""
    for name in ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_BACKUP_KEY'):
        monkeypatch.delenv(name, raising=False)

import pytest

from multi_llm_mcp import PROVIDERS, get_client


def test_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_client("nope")


def test_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        get_client("groq")


def test_ollama_needs_no_key():
    client = get_client("ollama")
    assert str(client.base_url).startswith(PROVIDERS["ollama"]["base_url"])

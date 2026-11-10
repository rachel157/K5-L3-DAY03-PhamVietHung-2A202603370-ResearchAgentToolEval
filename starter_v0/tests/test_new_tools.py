import pytest
from unittest.mock import patch, MagicMock
from tools.github_search.tool import github_search
from tools.hackernews.tool import hackernews
from tools.wikipedia.tool import wikipedia
from tools.save_note.tool import save_note

def test_github_search_empty_query():
    assert "error" in github_search(query="")

@patch("urllib.request.urlopen")
def test_github_search_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"items": [{"full_name": "a/b", "description": "d", "html_url": "u", "stargazers_count": 10, "language": "Python"}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    res = github_search(query="python")
    assert res["count"] == 1
    assert res["items"][0]["name"] == "a/b"

@patch("urllib.request.urlopen", side_effect=OSError("network unavailable"))
def test_github_search_exception(mock_urlopen):
    result = github_search(query="agent")
    assert "GitHub search failed" in result["error"]
    mock_urlopen.assert_called_once()

@patch("urllib.request.urlopen", side_effect=TimeoutError("timeout"))
def test_hackernews_timeout_returns_error(mock_urlopen):
    assert "HackerNews search failed" in hackernews(query="Rust")["error"]
    mock_urlopen.assert_called_once()

@patch("urllib.request.urlopen", side_effect=OSError("unavailable"))
def test_wikipedia_network_error_returns_error(mock_urlopen):
    assert "Wikipedia lookup failed" in wikipedia(title="Transformer")["error"]
    mock_urlopen.assert_called_once()

@patch("os.makedirs", side_effect=PermissionError("read only"))
def test_save_note_permission_error_returns_error(mock_makedirs):
    assert "Failed to save note" in save_note("note.md", "text", confirmed=True)["error"]

@pytest.mark.parametrize("confirmed", [False, "false", "true", 1, None])
@patch("builtins.open")
def test_save_note_requires_boolean_confirmation(mock_open, confirmed):
    result = save_note("note.md", "text", confirmed=confirmed)
    assert result["awaiting_user"] is True
    assert result["response_type"] == "yes_no"
    assert result["question"]
    mock_open.assert_not_called()

def test_save_note_writes_markdown_under_notes_directory(tmp_path, monkeypatch):
    import importlib
    module = importlib.import_module("tools.save_note.tool")
    monkeypatch.setattr(module, "NOTES_DIR", tmp_path / "notes")
    result = save_note("../example", "# Research", confirmed=True)
    assert result["success"] is True
    assert result["filename"] == "example.md"
    assert (tmp_path / "notes/example.md").read_text(encoding="utf-8") == "# Research"

@pytest.mark.parametrize("filename", ["", "  ", ".", "..", "/"])
def test_save_note_rejects_empty_or_directory_filename(filename):
    assert "error" in save_note(filename, "text", confirmed=True)

def test_save_note_rejects_non_text_content():
    assert "error" in save_note("note.md", {"text": "bad"}, confirmed=True)

@pytest.mark.parametrize("confirmed", [False, "false", "true", 1, None])
def test_send_requires_boolean_confirmation(confirmed, fake_http):
    from conftest import FakeResponse
    from tools.send.tool import send_telegram
    calls = fake_http(FakeResponse({"ok": True}))
    assert send_telegram("draft", confirmed=confirmed)["status"] == "needs_confirmation"
    assert calls == []

def test_hackernews_empty_query():
    assert "error" in hackernews(query="   ")

@patch("urllib.request.urlopen")
def test_hackernews_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"hits": [{"title": "HN", "url": "u", "points": 5, "author": "dev"}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    res = hackernews(query="ai")
    assert res["count"] == 1

def test_wikipedia_empty_title():
    assert "error" in wikipedia(title="")

@patch("urllib.request.urlopen")
def test_wikipedia_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"title": "Test", "extract": "Desc", "content_urls": {"desktop": {"page": "url"}}}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp
    res = wikipedia(title="Test")
    assert res["title"] == "Test"

def test_save_note_unconfirmed():
    res = save_note(filename="note.md", content="test", confirmed=False)
    assert res.get("awaiting_user") is True

def test_save_note_invalid_filename():
    assert "error" in save_note(filename="", content="test", confirmed=True)

@patch("os.makedirs")
@patch("builtins.open", new_callable=MagicMock)
def test_save_note_confirmed_success(mock_open, mock_makedirs):
    res = save_note(filename="note.md", content="# Test", confirmed=True)
    assert res.get("success") is True

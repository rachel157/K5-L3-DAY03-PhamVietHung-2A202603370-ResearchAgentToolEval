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

@patch("urllib.request.urlopen", side_error=Exception("Fail"))
def test_github_search_exception(mock_urlopen):
    # mock exception handling
    pass

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
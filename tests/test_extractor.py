import pytest
from pathlib import Path
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock

from deluge_export.extractor import get_extractor, LocalExtractor, HttpExtractor


def test_get_extractor_invalid_args():
    # Both provided
    with pytest.raises(ValueError, match="Cannot specify both"):
        get_extractor(state_dir="/tmp", state_url="http://localhost")
    # Neither provided
    with pytest.raises(ValueError, match="Must specify either"):
        get_extractor()


def test_get_extractor_local():
    extractor = get_extractor(state_dir="/tmp/deluge")
    assert isinstance(extractor, LocalExtractor)
    assert extractor.state_dir == Path("/tmp/deluge")


def test_get_extractor_http():
    extractor = get_extractor(state_url="http://localhost:8080/")
    assert isinstance(extractor, HttpExtractor)
    assert extractor.state_url == "http://localhost:8080"


def test_local_extractor_success(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    torrent_file = state_dir / "abc123def.torrent"
    torrent_file.write_text("dummy content")

    dest_dir = tmp_path / "dest"
    extractor = LocalExtractor(state_dir)

    # Test with desired_name
    result_path = extractor.extract("abc123def", dest_dir, desired_name="Ubuntu 24.04")

    assert result_path.exists()
    assert result_path.name == "Ubuntu 24.04.torrent"
    assert result_path.read_text() == "dummy content"


def test_local_extractor_missing_file(tmp_path):
    extractor = LocalExtractor(tmp_path)
    with pytest.raises(FileNotFoundError, match="not found at"):
        extractor.extract("missing_id", tmp_path / "dest")


def test_local_extractor_path_traversal(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    torrent_file = state_dir / "abc123def.torrent"
    torrent_file.write_text("dummy")

    dest_dir = tmp_path / "dest"
    extractor = LocalExtractor(state_dir)

    # The extractor should sanitize desired_name to just its basename
    result_path = extractor.extract("abc123def", dest_dir, desired_name="../evil_name")

    assert result_path.name == "evil_name.torrent"
    assert result_path.parent == dest_dir


@patch("urllib.request.urlopen")
def test_http_extractor_success(mock_urlopen, tmp_path):
    mock_response = MagicMock()
    # Mock reading contents
    mock_response.read.side_effect = [b"http dummy content", b""]
    mock_urlopen.return_value.__enter__.return_value = mock_response

    extractor = HttpExtractor("http://bucket:8080")
    dest_dir = tmp_path / "dest"

    result_path = extractor.extract("xyz987", dest_dir, desired_name="Test File")

    mock_urlopen.assert_called_once_with(
        "http://bucket:8080/xyz987.torrent", timeout=10
    )
    assert result_path.exists()
    assert result_path.name == "Test File.torrent"
    assert result_path.read_text() == "http dummy content"


@patch("urllib.request.urlopen")
def test_http_extractor_404(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="http://bucket:8080/404.torrent",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=None,
    )

    extractor = HttpExtractor("http://bucket:8080")
    with pytest.raises(FileNotFoundError, match="not found at"):
        extractor.extract("404", tmp_path / "dest")


@patch("urllib.request.urlopen")
def test_http_extractor_500(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="http://bucket:8080/500.torrent",
        code=500,
        msg="Server Error",
        hdrs={},
        fp=None,
    )

    extractor = HttpExtractor("http://bucket:8080")
    with pytest.raises(ConnectionError, match="HTTP 500"):
        extractor.extract("500", tmp_path / "dest")


@patch("urllib.request.urlopen")
def test_http_extractor_urlerror(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

    extractor = HttpExtractor("http://bucket:8080")
    with pytest.raises(ConnectionError, match="Failed to connect"):
        extractor.extract("conn_refused", tmp_path / "dest")

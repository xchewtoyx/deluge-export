import pytest
from unittest.mock import MagicMock
from deluge_export.client import get_matching_torrents

def test_get_matching_torrents_invalid_regex():
    client = MagicMock()
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        get_matching_torrents(client, "[invalid")

def test_get_matching_torrents_decoding_and_filtering():
    client = MagicMock()
    # Mocking deluge returned data shape (bytes keys and bytes values)
    client.call.return_value = {
        b"hash1": {b"name": b"Test 1", b"save_path": b"/data/test1", b"state": b"Seeding", b"total_size": 1024},
        b"hash2": {b"name": b"Another", b"save_path": b"/data/other", b"state": b"Downloading", b"total_size": 2048},
        b"hash3": {b"name": b"Match 2", b"save_path": b"/data/test2", b"state": b"Queued", b"total_size": 512},
    }

    # Match by name "Test"
    matches = get_matching_torrents(client, "Test")
    assert len(matches) == 1
    assert matches[0]["id"] == "hash1"
    assert matches[0]["name"] == "Test 1"
    
    # Match by path "other"
    matches = get_matching_torrents(client, "other")
    assert len(matches) == 1
    assert matches[0]["id"] == "hash2"
    assert matches[0]["save_path"] == "/data/other"

    # Match by pattern "test[12]" which hits multiple (by path)
    matches = get_matching_torrents(client, "test[12]")
    assert len(matches) == 2
    ids = {m["id"] for m in matches}
    assert ids == {"hash1", "hash3"}
    
    # Case insensitive check if provided in regex
    matches = get_matching_torrents(client, "(?i)another")
    assert len(matches) == 1
    assert matches[0]["id"] == "hash2"

def test_get_matching_torrents_missing_keys():
    # Verifies graceful handling if some keys are missing from the deluge response
    client = MagicMock()
    client.call.return_value = {
        b"hash4": {b"name": b"Missing Data"} # no save_path, state, total_size provided
    }
    matches = get_matching_torrents(client, "Missing")
    assert len(matches) == 1
    assert matches[0]["id"] == "hash4"
    assert matches[0]["name"] == "Missing Data"
    assert matches[0]["save_path"] == ""
    assert matches[0]["size"] == 0
    assert matches[0]["state"] == ""
    
    # Matching empty path
    matches_empty = get_matching_torrents(client, "Missing Data")
    assert len(matches_empty) == 1

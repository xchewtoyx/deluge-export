from deluge_client import DelugeRPCClient
from typing import List, Dict, Any
import re


def get_client(host: str, port: int, user: str, password: str) -> DelugeRPCClient:
    """Initialize and connect the Deluge RPC Client."""
    client = DelugeRPCClient(host, port, user, password)
    client.connect()
    return client


def get_matching_torrents(
    client: DelugeRPCClient, path_match: str
) -> List[Dict[str, Any]]:
    """
    Fetch torrents from deluge and filter by matching name or save_path
    against the provided regular expression.
    """
    # Fetch all torrents, getting specific properties to minimize data transfer
    # The b"" strings are required as deluge RPC uses bytestrings for keys
    torrents_data = client.call(
        "core.get_torrents_status", {}, [b"name", b"save_path", b"total_size", b"state"]
    )

    matches = []

    # Try compiling the regex pattern
    try:
        pattern = re.compile(path_match)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{path_match}': {e}")

    for torrent_id, data in torrents_data.items():
        # deluge-client returns raw bytes, we need to decode them
        decoded_id = torrent_id.decode("utf-8")
        name = data.get(b"name", b"").decode("utf-8")
        save_path = data.get(b"save_path", b"").decode("utf-8")
        size = data.get(b"total_size", 0)
        state = data.get(b"state", b"").decode("utf-8")

        # Check if the path or name match the provided regex
        if pattern.search(name) or pattern.search(save_path):
            matches.append(
                {
                    "id": decoded_id,
                    "name": name,
                    "save_path": save_path,
                    "size": size,
                    "state": state,
                }
            )

    return matches

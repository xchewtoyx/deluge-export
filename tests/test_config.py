import pytest
from pathlib import Path
from deluge_export.config import load_config

@pytest.fixture(autouse=True)
def uncache_config():
    # Clear the lru_cache between tests
    load_config.cache_clear()


def test_load_config_missing_file(monkeypatch):
    """Test when no config files exist."""
    def mock_exists(self): return False
    monkeypatch.setattr(Path, "exists", mock_exists)
    
    assert load_config() == {}


def test_load_config_valid_toml(tmp_path, monkeypatch):
    """Test reading a valid configuration file."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("[deluge]\nhost = 'test_host'\nport = 1234\n", encoding="utf-8")
    
    def mock_home(): return tmp_path
    monkeypatch.setattr(Path, "home", mock_home)
    # The code expects ~/.config/deluge-export/config.toml
    # For testing simpler paths, let's mock the list of paths in the function
    # Wait, the list is built dynamically from Path.home(), so we just need to place it there
    
    target_dir = tmp_path / ".config" / "deluge-export"
    target_dir.mkdir(parents=True)
    (target_dir / "config.toml").write_text("[deluge]\nuser = 'foo'\n", encoding="utf-8")

    config = load_config()
    assert config == {"user": "foo"}


def test_load_config_fallback_path(tmp_path, monkeypatch):
    """Test it uses the second path if the first doesn't exist."""
    def mock_home(): return tmp_path
    monkeypatch.setattr(Path, "home", mock_home)
    
    # Do not create the .config directory, but create the .deluge-export.toml
    (tmp_path / ".deluge-export.toml").write_text("[deluge]\nhost = 'second'\n", encoding="utf-8")
    
    assert load_config() == {"host": "second"}


def test_load_config_no_deluge_section(tmp_path, monkeypatch, capsys):
    """Test a valid TOML that is missing the [deluge] section entirely."""
    def mock_home(): return tmp_path
    monkeypatch.setattr(Path, "home", mock_home)
    
    (tmp_path / ".deluge-export.toml").write_text("[other]\nkey = 'value'\n", encoding="utf-8")
    
    assert load_config() == {}
    
    # Should print a warning to stderr
    captured = capsys.readouterr()
    assert "Warning: '[deluge]' section missing or invalid" in captured.err


def test_load_config_invalid_toml(tmp_path, monkeypatch, capsys):
    """Test encountering invalid TOML syntax."""
    def mock_home(): return tmp_path
    monkeypatch.setattr(Path, "home", mock_home)
    
    (tmp_path / ".deluge-export.toml").write_text("[deluge]\nuser 'bob'\n", encoding="utf-8") # Missing equals sign
    
    assert load_config() == {}
    
    captured = capsys.readouterr()
    assert "Warning: Failed to parse TOML file" in captured.err

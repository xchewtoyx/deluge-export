import abc
import shutil
import urllib.request
import urllib.error
from pathlib import Path

class BaseExtractor(abc.ABC):
    @abc.abstractmethod
    def extract(self, torrent_id: str, dest_dir: Path, desired_name: str | None = None) -> Path:
        """Extract the .torrent file to the destination directory. Returns the path to the extracted file."""
        pass

class LocalExtractor(BaseExtractor):
    def __init__(self, state_dir: str | Path):
        self.state_dir = Path(state_dir)
        
    def extract(self, torrent_id: str, dest_dir: Path, desired_name: str | None = None) -> Path:
        src_file = self.state_dir / f"{torrent_id}.torrent"
        if not src_file.exists():
            raise FileNotFoundError(f"Torrent file not found at {src_file}")
            
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"{desired_name}.torrent" if desired_name else f"{torrent_id}.torrent"
        dest_file = dest_dir / out_name
        
        shutil.copy2(src_file, dest_file)
        return dest_file

class HttpExtractor(BaseExtractor):
    def __init__(self, state_url: str):
        self.state_url = state_url.rstrip('/')
        
    def extract(self, torrent_id: str, dest_dir: Path, desired_name: str | None = None) -> Path:
        url = f"{self.state_url}/{torrent_id}.torrent"
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"{desired_name}.torrent" if desired_name else f"{torrent_id}.torrent"
        dest_file = dest_dir / out_name
        
        try:
            with urllib.request.urlopen(url) as response, open(dest_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        except urllib.error.HTTPError as e:
            if dest_file.exists():
                dest_file.unlink() # Cleanup partial/failed downloads
            raise FileNotFoundError(f"Failed to download torrent file from {url}: HTTP {e.code}")
        except urllib.error.URLError as e:
            if dest_file.exists():
                dest_file.unlink()
            raise ConnectionError(f"Failed to connect to {url}: {e.reason}")
        except Exception:
            if dest_file.exists():
                dest_file.unlink()
            raise
            
        return dest_file

def get_extractor(state_dir: str | None = None, state_url: str | None = None) -> BaseExtractor:
    if state_dir and state_url:
        raise ValueError("Cannot specify both state_dir and state_url")
    if state_dir:
        return LocalExtractor(state_dir)
    if state_url:
        return HttpExtractor(state_url)
    
    raise ValueError("Must specify either state_dir or state_url")

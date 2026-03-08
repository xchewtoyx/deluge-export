# deluge-export

A CLI application to search and extract torrents from a deluge server matching specific path patterns.

## Installation

You can install this repository locally for development using standard python tools.

Using `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

To avoid providing connection details on the CLI on every invocation, you can set up a configuration file.
The application will look for a TOML configuration file in the following locations (in order):
1. `~/.config/deluge-export/config.toml`
2. `~/.deluge-export.toml`

### Example `~/.deluge-export.toml`

```toml
[deluge]
host = "192.168.1.10" # Default: 127.0.0.1
port = 58846          # Default: 58846
user = "myuser"
password = "mypassword"
```

*Note: In TOML, string values MUST be wrapped with quotation marks.*

You can also provide configuration via Environment Variables: 
`DELUGE_HOST`, `DELUGE_PORT`, `DELUGE_USER`, `DELUGE_PASSWORD`

## Usage

You can invoke the application using the `dle` command if installed globally, or via `python -m deluge_export`.

To see all available commands and arguments:
```bash
dle --help
```

### Listing Matching Torrents

To view torrents matching a regex pattern on your deluge server without extracting them, use the `list` command.
The `--path-match` argument supports standard Python RegEx to match against the torrent's **name** or **save path**.

```bash
dle list --path-match "202[45]/11"

# Connection details can optionally be supplied manually
dle list --path-match "Ubuntu" --host bucket2 --user localclient --password supersecret
```

### Extracting Torrents (WIP)

_The logic to extract completed matching torrents to local disk is currently under active development._

```bash
dle extract --path-match "2025/11" --dest /path/to/extract/to
```

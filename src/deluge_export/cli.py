import typer
from pathlib import Path
from typing_extensions import Annotated
from deluge_export import client, config
from deluge_export.extractor import get_extractor

app = typer.Typer(help="Extracts torrents from a deluge server matching a pattern.")


def _get_connection_params(
    host: str | None, port: int | None, user: str | None, password: str | None
) -> tuple[str, int, str, str]:
    conf = config.load_config()
    final_host = str(host if host is not None else conf.get("host", "127.0.0.1"))
    raw_port = port if port is not None else conf.get("port", 58846)
    try:
        final_port = int(raw_port)
    except (ValueError, TypeError):
        typer.echo(
            f"Error: Invalid port value '{raw_port}'. Port must be an integer.",
            err=True,
        )
        raise typer.Exit(code=1)
    final_user = str(user if user is not None else conf.get("user", ""))
    final_password = str(password if password is not None else conf.get("password", ""))

    return final_host, final_port, final_user, final_password


@app.command("list")
def list_command(
    path_match: Annotated[
        str,
        typer.Option(
            "--path-match",
            help="Pattern to match the torrent name or save path against",
        ),
    ],
    host: Annotated[
        str | None,
        typer.Option("--host", envvar="DELUGE_HOST", help="Deluge daemon host"),
    ] = None,
    port: Annotated[
        int | None,
        typer.Option("--port", envvar="DELUGE_PORT", help="Deluge daemon port"),
    ] = None,
    user: Annotated[
        str | None,
        typer.Option("--user", envvar="DELUGE_USER", help="Deluge RPC username"),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password", envvar="DELUGE_PASSWORD", help="Deluge RPC password"
        ),
    ] = None,
):
    """
    List torrents matching a specified name or path pattern from the deluge server.
    """
    host, port, user, password = _get_connection_params(host, port, user, password)

    typer.echo(f"Connecting to Deluge at {host}:{port}...")
    try:
        deluge_client = client.get_client(host, port, user, password)
        typer.echo("Connected! Fetching torrents...")
        matches = client.get_matching_torrents(deluge_client, path_match)

        if not matches:
            typer.echo(f"No torrents found matching pattern: '{path_match}'")
            return

        typer.echo(f"\nFound {len(matches)} matching torrents:")
        typer.echo("-" * 80)

        for idx, match in enumerate(matches, 1):
            size_mb = match["size"] / (1024 * 1024)
            typer.echo(f"{idx}. {match['name']}")
            typer.echo(f"   ID: {match['id']}")
            typer.echo(f"   State: {match['state']}")
            typer.echo(f"   Size: {size_mb:.2f} MB")
            typer.echo(f"   Path: {match['save_path']}")
            typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error communicating with deluge: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def extract(
    path_match: Annotated[
        str,
        typer.Option(
            "--path-match",
            help="Pattern to match the torrent name or save path against",
        ),
    ],
    dest: Annotated[
        str,
        typer.Option("--dest", help="Destination path to extract .torrent files to"),
    ],
    state_dir: Annotated[
        str | None,
        typer.Option("--state-dir", help="Local path to the deluge state directory"),
    ] = None,
    state_url: Annotated[
        str | None,
        typer.Option("--state-url", help="HTTP URL to the deluge state directory"),
    ] = None,
    host: Annotated[
        str | None,
        typer.Option("--host", envvar="DELUGE_HOST", help="Deluge daemon host"),
    ] = None,
    port: Annotated[
        int | None,
        typer.Option("--port", envvar="DELUGE_PORT", help="Deluge daemon port"),
    ] = None,
    user: Annotated[
        str | None,
        typer.Option("--user", envvar="DELUGE_USER", help="Deluge RPC username"),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password", envvar="DELUGE_PASSWORD", help="Deluge RPC password"
        ),
    ] = None,
):
    """
    Extract torrents matching a specified name or path pattern to a destination directory.
    """
    host, port, user, password = _get_connection_params(host, port, user, password)

    if state_dir is None and state_url is None:
        typer.echo(
            "Error: You must provide either --state-dir or --state-url to locate the .torrent files.",
            err=True,
        )
        raise typer.Exit(code=1)
    if state_dir is not None and state_url is not None:
        typer.echo("Error: Cannot provide both --state-dir and --state-url.", err=True)
        raise typer.Exit(code=1)

    try:
        extractor = get_extractor(state_dir=state_dir, state_url=state_url)
    except Exception as e:
        typer.echo(f"Error initializing extractor: {e}", err=True)
        raise typer.Exit(code=1)

    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Connecting to Deluge at {host}:{port}...")
    try:
        deluge_client = client.get_client(host, port, user, password)
        typer.echo("Connected! Fetching torrents...")
        matches = client.get_matching_torrents(deluge_client, path_match)

        if not matches:
            typer.echo(f"No torrents found matching pattern: '{path_match}'")
            return

        typer.echo(
            f"\nFound {len(matches)} matching torrents. Starting extraction to {dest_path.absolute()}..."
        )

        success_count = 0
        for idx, match in enumerate(matches, 1):
            torrent_id = match["id"]
            name = match["name"]

            # Sanitize the torrent name for the filesystem
            safe_name = "".join(c for c in name if c.isalnum() or c in " ._-").strip()
            if not safe_name:
                safe_name = torrent_id

            typer.echo(f"[{idx}/{len(matches)}] Extracting {name}...", nl=False)
            try:
                out_file = extractor.extract(
                    torrent_id, dest_path, desired_name=safe_name
                )
                typer.echo(f" Done! -> {out_file.name}")
                success_count += 1
            except Exception as e:
                typer.echo(f" Failed! ({e})")

        typer.echo(
            f"\nSuccessfully extracted {success_count}/{len(matches)} .torrent files."
        )

        if success_count != len(matches):
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

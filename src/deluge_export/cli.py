import typer
from typing_extensions import Annotated
from deluge_export import client, config

app = typer.Typer(help="Extracts torrents from a deluge server matching a pattern.")


@app.command("list")
def list_command(
    path_match: Annotated[
        str, typer.Option("--path-match", help="Pattern to match the path against")
    ],
    host: Annotated[
        str, typer.Option("--host", envvar="DELUGE_HOST", help="Deluge daemon host")
    ] = config.DEFAULT_CONFIG.get("host", "127.0.0.1"),
    port: Annotated[
        int, typer.Option("--port", envvar="DELUGE_PORT", help="Deluge daemon port")
    ] = config.DEFAULT_CONFIG.get("port", 58846),
    user: Annotated[
        str, typer.Option("--user", envvar="DELUGE_USER", help="Deluge RPC username")
    ] = config.DEFAULT_CONFIG.get("user", ""),
    password: Annotated[
        str,
        typer.Option(
            "--password", envvar="DELUGE_PASSWORD", help="Deluge RPC password"
        ),
    ] = config.DEFAULT_CONFIG.get("password", ""),
):
    """
    List torrents matching a specified path pattern from the deluge server.
    """
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
        str, typer.Option("--path-match", help="Pattern to match the path against")
    ],
    dest: Annotated[
        str,
        typer.Option("--dest", help="Destination path to extract .torrent files to"),
    ],
    state_dir: Annotated[
        str,
        typer.Option("--state-dir", help="Local path to the deluge state directory"),
    ] = "",
    state_url: Annotated[
        str, typer.Option("--state-url", help="HTTP URL to the deluge state directory")
    ] = "",
    host: Annotated[
        str, typer.Option("--host", envvar="DELUGE_HOST", help="Deluge daemon host")
    ] = config.DEFAULT_CONFIG.get("host", "127.0.0.1"),
    port: Annotated[
        int, typer.Option("--port", envvar="DELUGE_PORT", help="Deluge daemon port")
    ] = config.DEFAULT_CONFIG.get("port", 58846),
    user: Annotated[
        str, typer.Option("--user", envvar="DELUGE_USER", help="Deluge RPC username")
    ] = config.DEFAULT_CONFIG.get("user", ""),
    password: Annotated[
        str,
        typer.Option(
            "--password", envvar="DELUGE_PASSWORD", help="Deluge RPC password"
        ),
    ] = config.DEFAULT_CONFIG.get("password", ""),
):
    """
    Export .torrent files matching a specified path pattern to a destination directory.
    """
    if not state_dir and not state_url:
        typer.echo(
            "Error: You must provide either --state-dir or --state-url to locate the .torrent files.",
            err=True,
        )
        raise typer.Exit(code=1)
    if state_dir and state_url:
        typer.echo("Error: Cannot provide both --state-dir and --state-url.", err=True)
        raise typer.Exit(code=1)

    from deluge_export.extractor import get_extractor

    try:
        extractor = get_extractor(
            state_dir=state_dir or None, state_url=state_url or None
        )
    except Exception as e:
        typer.echo(f"Error initializing extractor: {e}", err=True)
        raise typer.Exit(code=1)

    dest_path = __import__("pathlib").Path(dest)
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

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

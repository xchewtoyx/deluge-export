import typer
from typing_extensions import Annotated
from deluge_export import client

app = typer.Typer(help="Extracts torrents from a deluge server matching a pattern.")

@app.command("list")
def list_command(
    path_match: Annotated[str, typer.Option("--path-match", help="Pattern to match the torrent name or save path against")],
    host: Annotated[str, typer.Option("--host", help="Deluge daemon host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Deluge daemon port")] = 58846,
    user: Annotated[str, typer.Option("--user", help="Deluge RPC username")] = "",
    password: Annotated[str, typer.Option("--password", help="Deluge RPC password")] = ""
):
    """
    List torrents matching a specified name or path pattern from the deluge server.
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
            size_mb = match['size'] / (1024 * 1024)
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
        str, typer.Option("--path-match", help="Pattern to match the torrent name or save path against")
    ],
    dest: Annotated[str, typer.Option("--dest", help="Destination path to extract to")],
):
    """
    Extract torrents matching a specified name or path pattern to a destination directory.
    """
    typer.echo(f"Extracting torrents matching '{path_match}' to '{dest}'")
    # Implementation logic will go here


if __name__ == "__main__":
    app()

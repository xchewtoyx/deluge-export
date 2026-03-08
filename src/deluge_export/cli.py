import typer
from typing_extensions import Annotated

app = typer.Typer(help="Extracts torrents from a deluge server matching a pattern.")


@app.command()
def extract(
    path_match: Annotated[
        str, typer.Option("--path-match", help="Pattern to match the path against")
    ],
    dest: Annotated[str, typer.Option("--dest", help="Destination path to extract to")],
):
    """
    Extract torrents matching a specified path pattern to a destination directory.
    """
    typer.echo(f"Extracting torrents matching '{path_match}' to '{dest}'")
    # Implementation logic will go here


if __name__ == "__main__":
    app()

"""Command line interface to interact with the database."""
from typing import List
import click
import requests
from datetime import datetime, timedelta

from tabulate import tabulate
from mypackage.model import ReleaseDenorm
from mypackage.music_data import DB_NAME, get_releases_by_date, update_releases_db

BASE_URL = "http://localhost:8000"

@click.group()
def cli():
    """Just the CLI."""
    pass


@cli.group()
def artist():
    """Group for artist related commands."""
    pass


def add_artist(name):
    """
    Add a new artist with the given name by sending a POST request to the API.

    :param name: The name of the artist to add.
    """
    artist = {"nickname": name}
    response = requests.post(f"{BASE_URL}/artists", json=artist)
    if response.ok:
        click.echo("Artist added successfully!")
    else:
        click.echo(f"Error adding artist: {response.text}")


@click.command()
@click.option("--name", prompt=True, help="The name of the artist to add.")
def add(name):
    """
    Add a new artist with the given name by sending a POST request to the API.

    Example usage: `python app.py add --name 'The Beatles'`

    :param name: The name of the artist to add.
    """
    add_artist(name)


@artist.command()
@click.option("--name")
def delete(name):
    """Delete an artist from the database."""
    if not name:
        # List all artists and prompt the user to select one
        response = requests.get(f"{BASE_URL}/artists")
        response.raise_for_status()
        artists = response.json()
        choices = "\n".join(
            f"{artist['id']}: {artist['nickname']}" for artist in artists
        )
        artist_id = click.prompt(f"Select artist to delete:\n{choices}", type=int)

        # Get the nickname of the selected artist
        name = next(
            artist["nickname"] for artist in artists if artist["id"] == artist_id
        )

    # Delete the artist with the matching ID
    response = requests.delete(f"{BASE_URL}/artists/{artist_id}")
    response.raise_for_status()
    if response.status_code == 200 or response.status_code == 204:
        click.echo(f"Artist '{name}' (id: {artist_id}) deleted successfully!")
    elif response.status_code == 404:
        click.echo("Artist not found.")
    else:
        click.echo(f"Error deleting artist: {response.text}")


@artist.command()
def list_artists():
    """List all artists in the database."""
    response = requests.get("http://localhost:8000/artists")
    if response.status_code == 200:
        for artist in response.json():
            click.echo(
                f"{artist['id']} - {artist['nickname']} ({artist['last_checked']})"
            )
    else:
        click.echo(f"Error getting artists: {response.text}")


@cli.command()
def update():
    update_releases_db()

@cli.command()
@click.option(
    "--date",
    default=(datetime.today() - timedelta(days=datetime.today().weekday())).strftime(
        "%Y%m%d"
    ),
    help="Date in format YYYYMMDD",
)
def new(date):
    """Return new releases based on the given date.

    It takes one argument `date`, which is the date of the new releases to be
    returned. The function first calls the `get_releases_by_date` function to
    retrieve all the releases for that given date from the database. It then
    extracts the required fields of the `ReleaseDenorm` object, creates a
    `unmap` function that returns a list of attributes for each release and uses
    it to create a table with the specific fields found. The table is formatted,
    and the headers and values are printed using the `tabulate` function.
    """
    releases = get_releases_by_date(date, DB_NAME)
    required_fields = [
        field
        for field in ReleaseDenorm.__fields__.keys()
        if ReleaseDenorm.__fields__[field].required
    ]

    def unmap(release: ReleaseDenorm, fields: List[str]):
        return [getattr(release, field) for field in fields]

    use_fields = ["release_date"] + required_fields

    print(
        tabulate(
            [unmap(release, use_fields) for release in releases],
            headers=use_fields,
        )
    )


if __name__ == "__main__":
    cli()

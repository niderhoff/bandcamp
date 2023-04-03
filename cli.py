import click
import requests

base_url = "http://localhost:8000"


@click.group()
def cli():
    pass


@cli.group()
def artist():
    pass


@artist.command()
@click.option("--name", prompt=True)
def add(name):
    artist = {"nickname": name}
    response = requests.post(f"{base_url}/artists", json=artist)
    if response.status_code == 200:
        click.echo("Artist added successfully!")
    else:
        click.echo(f"Error adding artist: {response.text}")


@artist.command()
@click.option("--name")
def delete(name):
    if not name:
        # List all artists and prompt the user to select one
        response = requests.get(f"{base_url}/artists")
        response.raise_for_status()
        artists = response.json()
        choices = "\n".join(f"{artist['id']}: {artist['nickname']}" for artist in artists)
        artist_id = click.prompt(f"Select artist to delete:\n{choices}", type=int)

        # Get the nickname of the selected artist
        name = next(artist["nickname"] for artist in artists if artist["id"] == artist_id)

    # Delete the artist with the matching ID
    response = requests.delete(f"{base_url}/artists/{artist_id}")
    response.raise_for_status()
    if response.status_code == 200 or response.status_code == 204:
        click.echo(f"Artist '{name}' (id: {artist_id}) deleted successfully!")
    elif response.status_code == 404:
        click.echo("Artist not found.")
    else:
        click.echo(f"Error deleting artist: {response.text}")



@artist.command()
def list():
    response = requests.get("http://localhost:8000/artists")
    if response.status_code == 200:
        for artist in response.json():
            click.echo(f"{artist['id']} - {artist['nickname']} ({artist['last_checked']})")
    else:
        click.echo(f"Error getting artists: {response.text}")


if __name__ == "__main__":
    cli()

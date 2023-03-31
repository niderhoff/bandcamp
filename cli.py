import click
import requests


@click.group()
def cli():
    pass


@cli.group()
def artist():
    pass


@artist.command()
@click.option("--name", prompt=True)
@click.option("--url", prompt=True)
def add(name, url):
    artist = {"name": name, "url": url}
    response = requests.post("http://localhost:8000/artist", json=artist)
    if response.status_code == 200:
        click.echo("Artist added successfully!")
    else:
        click.echo(f"Error adding artist: {response.text}")


@artist.command()
@click.argument("name")
def delete(name):
    response = requests.delete(f"http://localhost:8000/artist/{name}")
    if response.status_code == 200:
        click.echo("Artist deleted successfully!")
    elif response.status_code == 404:
        click.echo("Artist not found.")
    else:
        click.echo(f"Error deleting artist: {response.text}")


@artist.command()
def list():
    response = requests.get("http://localhost:8000/artist")
    if response.status_code == 200:
        artists = response.json()["artists"]
        for artist in artists:
            click.echo(f"{artist[0]} - {artist[1]} ({artist[2]})")
    else:
        click.echo(f"Error getting artists: {response.text}")


if __name__ == "__main__":
    cli()

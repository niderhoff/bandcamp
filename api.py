import sqlite3

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from tabulate import tabulate

from music_data import extract_music_data, get_new_music_data


def format_music_table(data):
    # Group the music data by artist, title, and release date
    grouped_data = {}
    for item in data:
        key = (item["artist"], item["title"], item["release_date"])
        if key not in grouped_data:
            grouped_data[key] = {"tracks": [], "item": item}
        grouped_data[key]["tracks"].extend([t["link"] for t in item["tracks"]])

    # Extract the table headers from the dictionary keys
    table_headers = ["Artist", "Title", "Release Date", "Link", "Tracks"]

    # Format the music data as a table using the tabulate library
    table_rows = []
    for key, data in grouped_data.items():
        artist, title, release_date = key
        link = data["item"]["link"]
        tracks = [[t] for t in data["tracks"]]
        tracks_table = tabulate(tracks, tablefmt="plain")
        table_rows.append([artist, title, release_date, link, tracks_table])
    table_str = tabulate(table_rows, headers=table_headers, tablefmt="html")
    return table_str


# Create the FastAPI instance
app = FastAPI()

# Define the SQLite database filename
DB_NAME = "artists.db"

# Define the schema of the "artist" table in the database
with sqlite3.connect(DB_NAME) as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS artist (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL
        )
        """
    )


# Define a Pydantic model for the artist object
class Artist(BaseModel):
    name: str
    url: HttpUrl


# Define the POST route to add a new artist to the database
@app.post("/artist")
async def add_artist(artist: Artist):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO artist (name, url)
            VALUES (?, ?)
            """,
            (artist.name, artist.url),
        )
        artist_id = cursor.lastrowid
        conn.commit()
    return {"id": artist_id, **artist.dict()}


def get_artist_urls():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT url
            FROM artist
            """
        )
        urls = [row[0] for row in cursor.fetchall()]
    return urls


# Define the GET route to retrieve all artist URLs from the database
@app.get("/artist/urls")
async def get_all_artist_urls():
    urls = get_artist_urls()
    return {"urls": urls}


# Define the GET route to retrieve all artists from the database
@app.get("/artist")
async def get_all_artists():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, url
            FROM artist
            """
        )
        artists = cursor.fetchall()
    return {"artists": artists}


# Define the DELETE route to remove an artist from the database
@app.delete("/artist/{name}")
async def delete_artist(name: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM artist
            WHERE name = ?
            """,
            (name,),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Artist not found")
        conn.commit()
    return {"message": f"{cursor.rowcount} artist(s) deleted"}


@app.get("/", response_class=HTMLResponse)
async def root():
    # Call extract_music_data() to update the database
    artist_urls = get_artist_urls()
    extract_music_data(artist_urls, DB_NAME)

    # Get the newest music data from the database
    music_data = get_new_music_data(DB_NAME, "20230101")

    # Format the music data as an HTML table
    table_str = format_music_table(music_data)

    # Construct the HTML response with the formatted table
    html_content = f"""
        <html>
            <head>
                <title>Music Data Table</title>
            </head>
            <body>
                {table_str}
            </body>
        </html>
    """
    return html_content


if __name__ == "__main__":
    # Run the server with the specified arguments
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)

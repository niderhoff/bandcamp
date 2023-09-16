'''
Ok now let's write a CRUD API with the fastapi package and sqlite3 which helps us to Create, delete, and read artists.

Everytime we access the database, please use our existing database context manager 'sqlite_db',
which we can import using 'from db import sqlite_db'. The Database schema of the Artist table looks like this:
"""
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT,
            last_checked TIMESTAMP
        )
"""

Please Provide the API Model for the Artist. Since the user only will every provide the nickname, we can leave all other fields optional and only use them when returning data to the user.
Write the following routes:
- list all artists
- list a particular artist with a provided id
- insert a new artist with a provided nickname
- delete a particular artist with a provided id
Every API route should return a response to the user.
'''

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Response, status

from .db import sqlite_db
from .model import Artist
from .music_data import DB_NAME, get_releases_by_date

app = FastAPI()

if not Path(DB_NAME).exists():
    sys.exit(f"{Path(DB_NAME).absolute()} does not exist.")
print(f"DB: {Path(DB_NAME).absolute()}")


@app.get("/releases")
@app.get("/releases/{date}")
def get_releases(date: Optional[str] = None) -> Response:
    """
    Retrieve a list of releases based on a given date (if provided) using data from a specified SQLite database.

    Args:
        date (str): A string format of a date (YYYYMMDD) for which to retrieve releases. Defaults to None.
    Returns:
        Response: A Response object with a list of releases in HTML table format.
    """
    if not date:
        last_thursday = datetime.today() - timedelta(
            days=datetime.today().weekday() + 3
        )
        date = last_thursday.strftime("%Y%m%d")

    releases = get_releases_by_date(date, DB_NAME)

    release_table = "\n".join(
        [
            f"<tr><td>{release.release_date}</td><td>{release.artist}</td><td>{release.title}</td><td><a href='{release.link}'>{release.link}</a></td></tr>"
            for release in releases
        ]
    )

    table_html = f"""
<html>
    <head>
        <title>Releases since {date}</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.0/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container">
            <h1>Releases since {date}</h1>
            <table class="table table-striped table-bordered">
                <thead class="thead-light">
                    <tr>
                        <th>Release Date</th>
                        <th>Artist</th>
                        <th>Title</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
                    {release_table}
                </tbody>
            </table>
        </div>
    </body>
</html>
    """

    return Response(content=table_html, media_type="text/html")


@app.get("/artists", response_model=List[Artist])
def list_artists() -> List[Artist]:
    """List all registered artists."""
    with sqlite_db(DB_NAME) as conn:
        print(Path(DB_NAME).absolute())
        cursor = conn.cursor()
        cursor.execute("SELECT id, nickname, last_checked FROM artists")
        rows = cursor.fetchall()
        return [Artist(id=row[0], nickname=row[1], last_checked=row[2]) for row in rows]


@app.get("/artists/{artist_id}", response_model=Artist)
def get_artist(artist_id: int) -> Artist:
    """Get artist info from DB."""
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nickname, last_checked FROM artists WHERE id = ?", (artist_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found"
            )
        return Artist(id=row[0], nickname=row[1], last_checked=row[2])


@app.post("/artists", response_model=Artist)
def create_artist(artist: Artist) -> Artist:
    """Add new artist to the DB."""
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO artists (nickname) VALUES (?)", (artist.nickname,))
        artist_id = cursor.lastrowid
        conn.commit()
        return Artist(id=artist_id, nickname=artist.nickname, last_checked=None)


@app.delete("/artists/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artist(artist_id: int):
    """Delete artist from the DB."""
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM artists WHERE id = ?", (artist_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found"
            )
        conn.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bc_agent.api:app", host="0.0.0.0", port=8000, workers=1, reload=True)

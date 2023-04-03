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

from music_data import DB_NAME

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Artist(BaseModel):
    id: Optional[int]
    nickname: str
    last_checked: Optional[datetime]

from fastapi import FastAPI, HTTPException, status
from typing import List

from db import sqlite_db


app = FastAPI()


@app.get("/artists", response_model=List[Artist])
def list_artists():
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nickname, last_checked FROM artists")
        rows = cursor.fetchall()
        return [Artist(id=row[0], nickname=row[1], last_checked=row[2]) for row in rows]


@app.get("/artists/{artist_id}", response_model=Artist)
def get_artist(artist_id: int):
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nickname, last_checked FROM artists WHERE id = ?", (artist_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")
        return Artist(id=row[0], nickname=row[1], last_checked=row[2])


@app.post("/artists", response_model=Artist)
def create_artist(artist: Artist):
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO artists (nickname) VALUES (?)", (artist.nickname,))
        artist_id = cursor.lastrowid
        conn.commit()
        return Artist(id=artist_id, nickname=artist.nickname, last_checked=None)


@app.delete("/artists/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artist(artist_id: int):
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM artists WHERE id = ?", (artist_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artist not found")
        conn.commit()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, workers=1)
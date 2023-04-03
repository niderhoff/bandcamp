from contextlib import contextmanager
import sqlite3


@contextmanager
def sqlite_db(db_name):
    if not db_name.endswith(".db"):
        raise ValueError("Not a SQLite database")

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS artists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT,
            last_checked TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY,
            artist_id INTEGER,
            title TEXT,
            release_date TIMESTAMP,
            link TEXT,
            FOREIGN KEY (artist_id) REFERENCES artists(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY,
            release_id INTEGER,
            number INTEGER,
            title TEXT,
            duration TEXT,
            link TEXT,
            FOREIGN KEY (release_id) REFERENCES releases(id)
        )
    """
    )

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

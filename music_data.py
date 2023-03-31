import datetime
import json
import re
import sqlite3
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tabulate import tabulate


def extract_music_items_from_url(url):
    # Check that the URL is valid
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        print(f"Invalid URL: {url}")
        return []

    # Extract all music items from the website's HTML
    soup = BeautifulSoup(response.text, "html.parser")
    music_items = []
    music_grid = soup.find("ol", {"class": "music-grid"})
    if music_grid:
        music_items = music_grid.find_all("li", {"class": "music-grid-item"})

    # Extract only the title and "art" image URL from each music item
    result = []
    for item in music_items:
        item_dict = {"title": "", "art_url": "", "link": ""}
        art_div = item.find("div", {"class": "art"})
        if art_div:
            item_dict["art_url"] = art_div.find("img").attrs.get("src", "").strip()
        title_p = item.find("p", {"class": "title"})
        if title_p:
            item_dict["title"] = title_p.text.strip()
        link_a = item.find("a", href=True)
        if link_a:
            item_dict["link"] = link_a["href"].strip()
        result.append(item_dict)

    return result


def extract_track_info_from_links(music_items, base_url):
    parsed_url = urlparse(base_url)
    default_artist_name = parsed_url.netloc.split(".")[0]
    for item in music_items:
        link = item["link"]
        print(f"grabbing title information for {link}")
        if link:
            absolute_link = urljoin(base_url, link)
            try:
                response = requests.get(absolute_link)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                print(f"Error retrieving link HTML: {absolute_link}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            artist_header = soup.find("h3", string="by")
            if artist_header:
                artist_a = artist_header.find("a", href=True)
                if artist_a:
                    artist_name = artist_a.text.strip()
                else:
                    artist_name = default_artist_name
            else:
                artist_name = default_artist_name

            release_date_elem = soup.find(
                "div", {"class": "tralbumData tralbum-credits"}
            )
            if release_date_elem:
                release_date_match = re.search(
                    r"released\s+(.+)\n\s+\n", release_date_elem.text, re.IGNORECASE
                )
                if release_date_match:
                    release_date_str = release_date_match.group(1).strip()
                    try:
                        release_date = datetime.datetime.strptime(
                            release_date_str, "%B %d, %Y"
                        )
                        release_date = release_date.strftime("%Y-%m-%d")
                    except ValueError:
                        release_date = ""
                else:
                    release_date = ""
            else:
                release_date = ""

            item["release_date"] = release_date
            item["artist"] = artist_name

            track_table = soup.find("table", {"id": "track_table"})
            if track_table:
                title_cols = track_table.find_all("td", {"class": "title-col"})
                track_info_list = []
                for title_col in title_cols:
                    track_dict = {"link": "", "title": "", "time": "", "artist": ""}
                    link_a = title_col.find("a", href=True)
                    if link_a:
                        track_dict["link"] = link_a["href"].strip()
                    track_title = title_col.find("span", {"class": "track-title"})
                    if track_title:
                        track_dict["title"] = track_title.text.strip()
                    time_span = title_col.find("span", {"class": "time"})
                    if time_span:
                        track_dict["time"] = time_span.text.strip()
                    track_dict["artist"] = artist_name
                    track_info_list.append(track_dict)

                item["tracks"] = track_info_list

    return music_items


def create_music_data_table(conn):
    c = conn.cursor()

    # Create the music_data table if it doesn't exist
    c.execute(
        "CREATE TABLE IF NOT EXISTS music_data ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "title TEXT, "
        "artist TEXT, "
        "release_date TEXT, "
        "art_url TEXT, "
        "link TEXT UNIQUE, "
        "tracks TEXT)"
    )

    # Check if the music_data table has necessary columns
    c.execute("PRAGMA table_info('music_data')")
    columns = set(col[1] for col in c.fetchall())
    expected_columns = {
        "id",
        "title",
        "artist",
        "release_date",
        "art_url",
        "link",
        "tracks",
    }
    missing_columns = expected_columns - columns

    if missing_columns:
        # Add missing columns to the music_data table
        for col in missing_columns:
            c.execute(f"ALTER TABLE music_data ADD COLUMN {col} TEXT")

    unexpected_columns = columns - expected_columns
    if unexpected_columns:
        # Raise an error if unexpected columns are found
        raise ValueError(
            f"Unexpected columns in music_data table: {unexpected_columns}"
        )


def extract_music_data(urls, db_filename):
    # Load existing items from the database
    existing_items = set()
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    try:
        create_music_data_table(conn)

        # Load existing items from the database
        c.execute("SELECT link FROM music_data")
        for row in c:
            existing_items.add(row[0])

        # Extract music data from each URL
        music_data = []
        for url in urls:
            music_items = extract_music_items_from_url(url)
            print(f"found {len(music_items)} items on {url}")
            for item in music_items:
                link = item.get("link")
                if link and link not in existing_items:
                    extract_track_info_from_links([item], url)
                    music_data.append(item)

        # Save new music data to the database
        save_music_data_to_db(music_data, conn)

        # Return sorted music data by release date
        return sorted(music_data, key=lambda x: x.get("release_date"))

    except sqlite3.Error as e:
        print(f"Error: {e}")
        conn.rollback()

    finally:
        conn.close()


def save_music_data_to_db(music_data, conn):
    c = conn.cursor()

    try:
        create_music_data_table(conn)

        # Insert each item in the music data list into the table
        for item in music_data:
            title = item.get("title")
            artist = item.get("artist")
            release_date = item.get("release_date")
            art_url = item.get("art_url")
            link = item.get("link")
            tracks = item.get("tracks")
            if tracks:
                tracks_json = json.dumps(tracks)
            else:
                tracks_json = None

            c.execute(
                "INSERT OR IGNORE INTO music_data (title, artist, release_date, art_url, link, tracks) "
                "VALUES (?, ?, ?, ?, ?, json(?))",
                (title, artist, release_date, art_url, link, tracks_json),
            )

        # Commit the changes
        conn.commit()

    except sqlite3.Error as e:
        print(f"Error: {e}")
        conn.rollback()


def get_new_music_data(db_filename, release_date_str):
    # Parse release_date_str into a datetime object
    release_date = datetime.datetime.strptime(release_date_str, "%Y%m%d").date()

    # Connect to the database and retrieve music data with newer release dates
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute(
        """SELECT id,
                        coalesce(title, ''),
                        coalesce(artist, ''),
                        coalesce(release_date, ''),
                        coalesce(art_url, ''),
                        coalesce(link, ''),
                        coalesce(tracks, '[]')
                 FROM music_data
                 WHERE release_date > ?""",
        (release_date,),
    )
    rows = c.fetchall()

    # Convert the rows to a list of dictionaries
    music_data = [
        {
            "id": row[0],
            "title": row[1],
            "artist": row[2],
            "release_date": row[3],
            "art_url": row[4],
            "link": row[5],
            "tracks": json.loads(row[6]),
        }
        for row in rows
    ]

    # Close the database connection and return the music data
    conn.close()
    return music_data


def print_music_data_table(music_data):
    """
    Prints a table of music data to the console, grouping tracks by artist, title, and release date.
    """
    # Group the music data by artist, title, and release date
    grouped_data = {}
    for item in music_data:
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
    table_str = tabulate(table_rows, headers=table_headers)

    # Print the table to the console
    print(table_str)

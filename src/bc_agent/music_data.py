'''
Written by ChatGPT using the following prompt.

You are a backend developer proficient in python and we are together working on a project. Here's a summary of the project so far:
* The goal of the project is to create a tool in Python to track new releases coming out from artists we follow.
* So far, we have implemented the core functionality of the tool, including error handling for network and HTTP issues, missing data, and incorrect input types.

The Requirements are as follows:

* Given a list of saved artist_nicknames, we will visit the bandcamp artist page at https://artist_nickname.bandcamp.com where we can see all music releases from that artist.
* We will download the page using requests and and parse the html with beautifulsoup.
* We have defined a get_new_releases function that takes a user provided artist_nickname as input and returns list of dataclasses representing new releases from that artist.
* The get_new_releases function first checks that the input argument is valid and that the artist subdomain is valid (all characters should be valid parts of an URL). It will then proceed to download the HTML from bandcamp, handling any possible HTTP errors.
* For each artist subdomain, the function downloads the HTML from the Bandcamp page and extracts a list of urls to all releases of that artist.
* The release can be found inside a html list '<ol class="music-grid">' object. Each list item looks like '<li class="music-grid-item">' and contains the link as well as title of that release.
* The links of all releases are relative links will be added to a list. Since they are relative links, we will join them with the artist page using a proper method of joining urls. After we have finished, we will log a message stating how many release we have found.
* In the next step, we will loop over the list and call the function extract_title_metadata on all list elements.

* The function extract_title_metadata takes one argument which is a link to a bandcamp release page. We will make sure that the argument passed by the user is actually a valid link.
* We will download that website using requests and extract the following information from the html using beautifulsoup:
    - title: string
    - artist_name: string
    - release_date: string
    - list of tracks: a list of 'track' dataclass instances.
* The artist name can be extract from an html object which looks like this:
"""
<h3 style="margin:0px;">by
        <span>
          <a href="https://bookashade.bandcamp.com">Booka Shade</a>
          </span>

        </h3>
"""
* The title name can be extracted from this html object:
"""
<h2 class="trackTitle">
            Twisted Cadence [Single]

        </h2>
"""
* The release date can be extracted from this object:
"""
<div class="tralbumData tralbum-credits">
                released March 10, 2023
            <br>...
            </div>
"""
* The list of tracks can be extracted from this html table:
"""
<table class="track_list track_table" id="track_table">
<tbody><tr class="track_row_view linked" rel="tracknum=1">
<td class="play-col"><a role="button" aria-label="Play Twisted Cadence"><div class="play_status"></div></a></td>
<td class="track-number-col"><div class="track_number secondaryText">1.</div></td>
<td class="title-col">
    <div class="title">
        <a href="/track/twisted-cadence"><span class="track-title">Twisted Cadence</span></a>
        <span class="time secondaryText">
            04:40
        </span>
    </div>
</td>
<td class="info-col"><div class="info_link"><a href="/track/twisted-cadence"></a></div></td>
<td class="download-col">
<div class="dl_link">
<a href="/track/twisted-cadence?action=download">
        buy track
</a>
</div></td>
</tr>
</tbody></table>
"""
* For each track we want to extract the track_number, title, link and time and store it into a "Track"-dataclass.
* The extracted information for all releases will be returned as a list of "Release"-dataclasses.

Do you have any questions regarding the requirements?

> No, the requirements are clear and detailed. However, I would like to clarify a few things:
> Can we assume that the user will always provide valid artist nicknames? If not, how should we handle invalid input?
> What should be the format of the output of the get_new_releases function? Should it be a list of Release-dataclasses or something else?
> How do you want the logging to be handled? Should we write the log messages to a file or print them to the console?

1. the artist nicknames should only contain alphanumeric characters as well as underline (_) and dash (-). Please validate the input accordingly.
2. yes the output should be a list of Release dataclasses.
3. we should write log messages to stdout using the INFO loglevel.

> Understood. Here are a few more questions to clarify the requirements:
> Can we assume that all releases will have at least one track or should we handle the case where no tracks are available?
> How should we handle errors that occur during the extraction of metadata for a specific release? Should we skip that release and move on to the next one, or should we terminate the entire process and raise an exception?

1. we can assume all releases have at least 1 track.
2. if the extraction of metadata fails for a given release, we should skip this one, log an error and move on to the next one.

> Got it, thanks for clarifying. Here are some additional questions:
> Should we include the duration of each track in the Track dataclass or just the title, link, and track number?
> Should we use a specific date format for the release_date field in the Release dataclass, or can we use any format as long as it's a string?
> Should we assume that all releases will have the same number of tracks, or can they vary in number?

1. we should include the duration
2. for now we can keep it as a string.
3. every release has a different number of tracks.

> Thank you for clarifying. Here are a few more questions:
> Should the Track dataclass include the duration in seconds or in some other format?
> Should we include the total duration of a release in the Release dataclass, or should this be calculated elsewhere if needed?
> Should we include any additional metadata for a release or a track, such as genre or album art?

1. it can just be a string.
2. this is not necessary.
3. no additional metadata

> Understood, thank you for clarifying. Here are a few more questions:
> Should we handle cases where a release has multiple discs or parts with different track listings?
> Should we handle cases where a release has multiple versions, such as a regular version and a deluxe version with bonus tracks?
> Should we handle cases where a release has been removed from the Bandcamp artist page, but metadata is still available through other sources, such as APIs or web scraping other websites?

1. that is not necessary.
2. that is also not necessary.
3. that is not necessary.

I think we can start the implementation now.

> Great, let's get started! If you have any questions or need any further clarification during the implementation process, please don't hesitate to ask.

please provide me now with the code
'''

import logging
import re
from datetime import datetime
from typing import List

import requests
from bs4 import BeautifulSoup

from .db import sqlite_db
from .model import ReleaseDenorm, Track

logging.basicConfig(level=logging.INFO)

DB_NAME = "bandcamp.db"


def get_new_releases(artist_nickname: str) -> List[ReleaseDenorm]:
    """Get new releases from bandcamp artist page."""
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()

        # Check if the artist exists in the database
        cursor.execute("SELECT id FROM artists WHERE nickname = ?", (artist_nickname,))
        artist_id = cursor.fetchone()
        if not artist_id:
            # Add the artist to the database if it doesn't exist
            cursor.execute(
                "INSERT INTO artists (nickname, last_checked) VALUES (?, ?)",
                (artist_nickname, datetime.now()),
            )
            artist_id = cursor.lastrowid
            conn.commit()
        else:
            artist_id = artist_id[0]

        # Get all release URLs and release dates for the artist from the database
        cursor.execute(
            "SELECT link, release_date FROM releases WHERE artist_id = ?", (artist_id,)
        )
        existing_releases = {row[0]: row[1] for row in cursor.fetchall()}

    artist_url = f"https://{artist_nickname}.bandcamp.com"
    response = requests.get(artist_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    release_urls = [
        a["href"] for a in soup.find("ol", {"class": "music-grid"}).find_all("a")
    ]
    release_urls = [artist_url + link for link in release_urls]

    # Find new release links that are not already in the database
    new_release_urls = set(release_urls) - set(existing_releases.keys())

    logging.info(f"Found {len(release_urls)} releases for artist {artist_nickname}")
    logging.info(
        f"{len(new_release_urls)} new releases found for artist {artist_nickname}"
    )

    new_releases: List[ReleaseDenorm] = []
    for release_url in new_release_urls:
        try:
            release = extract_title_metadata(release_url)
            if release.link not in existing_releases:
                new_releases.append(release)
        except Exception as e:
            logging.error(
                f"Error extracting metadata for release at {release_url}: {e}",
                exc_info=True,
            )

    # Save new releases to the database
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()

        for release in new_releases:
            # Add release to the database
            cursor.execute(
                "INSERT INTO releases (artist_id, title, release_date, link) VALUES (?, ?, ?, ?)",
                (artist_id, release.title, release.release_date, release.link),
            )
            release_id = cursor.lastrowid

            # Add tracks to the database
            for track in release.tracks:
                cursor.execute(
                    "INSERT INTO tracks (release_id, number, title, duration, link) VALUES (?, ?, ?, ?, ?)",
                    (release_id, track.number, track.title, track.duration, track.link),
                )

        conn.commit()

    return new_releases


def extract_title_metadata(release_url: str) -> ReleaseDenorm:
    """Extract title metadata from the bandcamp release page."""
    logging.info(f"Extracting metadata from release at {release_url}")
    response = requests.get(release_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.find("h2", {"class": "trackTitle"}).text.strip()
    artist = soup.find("h3").find("a").text.strip()

    # Extract the release date from the tralbumData div using regex
    date_str = soup.find("div", {"class": "tralbumData"}).text.strip()
    match = re.search(r"released (.+)", date_str)
    release_date_str = match.group(1) if match else ""

    # Parse the release date string into a datetime object
    release_date = (
        datetime.strptime(release_date_str, "%B %d, %Y") if release_date_str else None
    )

    tracks_table = soup.find("table", {"id": "track_table"})
    tracks = []
    for row in tracks_table.find_all("tr"):
        try:
            number_str = row.find("div", {"class": "track_number"}).text.strip()
            number = int("".join(filter(str.isdigit, number_str)))
            title = row.find("span", {"class": "track-title"}).text.strip()
            duration = row.find("span", {"class": "time"}).text.strip()
            track_url = (
                release_url
                + row.find("a", {"href": lambda href: href and "/track/" in href})[
                    "href"
                ]
            )
            tracks.append(Track(number, title, duration, track_url))
        except Exception as e:
            logging.error(
                f"Error extracting metadata for track in release at {release_url}: {e}",
                exc_info=True,
            )

    return ReleaseDenorm(title, artist, release_url, release_date, tracks)


def get_artist_nicknames_from_db():
    """Retrieve all artist nicknames from a sqlite database.

    Executes a SELECT query in the database and returns a list of all artist nicknames.

    Returns:
        artist_nicknames (list): A list of strings representing all artist nicknames in the database.
    """
    with sqlite_db(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nickname FROM artists")
        rows = cursor.fetchall()
        artist_nicknames = [row[0] for row in rows]
        return artist_nicknames


def update_releases_db():
    """
    Update the releases database for each artist nickname by fetching and adding new releases.

    Log any errors that occur during the process.
    """
    for artist_nickname in get_artist_nicknames_from_db():
        try:
            get_new_releases(artist_nickname)
        except Exception as e:
            logging.error(
                f"Error updating releases for artist {artist_nickname}: {e}",
                exc_info=True,
            )


def get_releases_by_date(date: str, db_name: str) -> List[ReleaseDenorm]:
    """Take in a date string in the format `YYYYMMDD` and a database filename as arguments.

    Then use a context manager to create a connection to the database and execute a SQL query to retrieve all releases with the
    given date. The results are then converted into a list of `Release` objects
    using the `pydantic` library and returned.
    """
    formatted_date = datetime.strptime(date, "%Y%m%d")
    with sqlite_db(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.title, a.nickname, r.link,r.release_date
            FROM releases r INNER JOIN artists a ON r.artist_id=a.id
            WHERE r.release_date >= ? ORDER BY r.release_date DESC
            """,
            (formatted_date,),
        )
        results = cursor.fetchall()
        releases = [
            ReleaseDenorm(title=row[0], artist=row[1], link=row[2], release_date=row[3])
            for row in results
        ]

        return releases


if __name__ == "__main__":
    update_releases_db()

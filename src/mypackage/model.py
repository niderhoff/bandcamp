"""Models for the Database and API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Artist(BaseModel):
    """Artist Model."""

    nickname: str
    id: Optional[int] = None
    last_checked: Optional[datetime] = None


class Release(BaseModel):
    """Normalized Release model (artist as foreign key)."""

    id: int
    artist_id: int
    title: str
    release_date: datetime
    link: str


class Track(BaseModel):
    """Track Model."""

    number: int
    title: str
    duration: str
    link: str
    id: Optional[int] = None
    release_id: Optional[int] = None


class ReleaseDenorm(BaseModel):
    """Denormalized Release class (artist is joined here)."""

    title: str
    artist: str
    link: str
    release_date: Optional[datetime] = None
    tracks: Optional[List[Track]]

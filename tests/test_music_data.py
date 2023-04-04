import pytest
from unittest.mock import MagicMock, patch

from mypackage.music_data import get_artist_nicknames_from_db


@pytest.fixture
def mock_sqlite_db():
    with patch("mypackage.music_data.sqlite_db") as mock:
        yield mock


def test_returns_artist_nicknames(mock_sqlite_db):
    # Arrange
    artist_nicknames = ["Artist 1", "Artist 2", "Artist 3"]
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(name,) for name in artist_nicknames]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_sqlite_db.return_value.__enter__.return_value = mock_conn

    # Act
    result = get_artist_nicknames_from_db()

    # Assert
    assert result == artist_nicknames
    mock_sqlite_db.assert_called_once_with("bandcamp.db")
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT nickname FROM artists")
    mock_cursor.fetchall.assert_called_once()

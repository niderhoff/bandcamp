'''
Now please write a pytest unit test which uses the requests library to test each api route. The example we will use is:
- nickname: new_artist

Make sure to test the return codes as well as response contents.
'''
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_list_artists():
    response = client.get("/artists/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_and_delete_artist_by_id():
    # Add a new artist to the database
    response = client.post("/artists/", json={"nickname": "new_artist"})
    artist_id = response.json()["id"]

    # Get the newly added artist by ID
    response = client.get(f"/artists/{artist_id}")
    assert response.status_code == 200
    assert response.json()["nickname"] == "new_artist"

    # Delete the newly added artist by ID
    response = client.delete(f"/artists/{artist_id}")
    assert response.status_code == 204


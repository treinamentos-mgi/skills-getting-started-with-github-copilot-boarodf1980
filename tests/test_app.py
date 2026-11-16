import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture
def sample_activities(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 3,
            "participants": ["current@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


def test_root_redirects_to_activity_page(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert response.url.path == expected_location
    assert response.history[0].status_code == 307


def test_get_activities_returns_activity_data(client, sample_activities):
    # Arrange
    expected_activities = sample_activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, sample_activities):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in sample_activities["Chess Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client, sample_activities):
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client, sample_activities):
    # Arrange
    email = "current@mergington.edu"
    original_participants = list(sample_activities["Chess Club"]["participants"])

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert sample_activities["Chess Club"]["participants"] == original_participants


def test_cancel_signup_removes_participant(client, sample_activities):
    # Arrange
    email = "current@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Canceled signup for {email} in Chess Club"}
    assert email not in sample_activities["Chess Club"]["participants"]


def test_cancel_signup_returns_not_found_for_unknown_activity(client, sample_activities):
    # Arrange
    email = "current@mergington.edu"

    # Act
    response = client.delete("/activities/Unknown/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_cancel_signup_returns_not_found_for_unregistered_participant(client, sample_activities):
    # Arrange
    email = "missing@mergington.edu"
    original_participants = list(sample_activities["Chess Club"]["participants"])

    # Act
    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert sample_activities["Chess Club"]["participants"] == original_participants
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    original_activities = deepcopy(app_module.activities)
    try:
        with TestClient(app_module.app) as test_client:
            yield test_client
    finally:
        app_module.activities.clear()
        app_module.activities.update(original_activities)


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"] == app_module.activities["Chess Club"]


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": "new.student@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@example.com for Soccer Club"
    }
    assert "new.student@example.com" in app_module.activities["Soccer Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_email_ignoring_case_and_whitespace(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "  MICHAEL@MERGINGTON.EDU  "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_full_activity_without_adding_participant(client):
    activity = app_module.activities["Soccer Club"]
    activity["max_participants"] = len(activity["participants"])

    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": "new.student@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert activity["participants"] == []


def test_unregister_removes_participant_ignoring_email_case(client):
    participants = app_module.activities["Soccer Club"]["participants"]
    participants.append("Case.Student@Example.com")

    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": "case.student@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered Case.Student@Example.com from Soccer Club"
    }
    assert participants == []


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"

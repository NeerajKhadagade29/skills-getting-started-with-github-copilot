"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestActivityEndpoints:
    """Test the activities endpoints"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Tennis Club" in data

    def test_get_activities_has_required_fields(self, client):
        """Test that activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email(self, client):
        """Test signing up with an email already registered"""
        # alex@mergington.edu is already in Basketball Team
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_updates_participant_list(self, client):
        """Test that signup actually adds the participant"""
        # Sign up a new student
        email = "teststudent@mergington.edu"
        client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        
        # Verify the student is in the participants list
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Tennis Club"]["participants"]


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successfully unregistering from an activity"""
        # First sign up
        email = "removeme@mergington.edu"
        client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Art Studio/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered(self, client):
        """Test unregistering when student is not registered"""
        response = client.delete(
            "/activities/Debate Team/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_removes_from_list(self, client):
        """Test that unregister actually removes the participant"""
        # Sign up first
        email = "unregistertest@mergington.edu"
        client.post(
            "/activities/Music Ensemble/signup",
            params={"email": email}
        )
        
        # Unregister
        client.delete(
            "/activities/Music Ensemble/unregister",
            params={"email": email}
        )
        
        # Verify removed from list
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Music Ensemble"]["participants"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

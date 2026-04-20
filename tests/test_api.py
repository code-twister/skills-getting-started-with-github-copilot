"""
Tests for the Mergington High School Activities API
Uses the AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a known state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        # Arrange
        expected_activity_count = 3
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activity_count
        for activity_name in expected_activities:
            assert activity_name in data

    def test_get_activities_contains_participants(self, client):
        """Test that activities include participant information"""
        # Arrange
        activity_name = "Chess Club"
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess = data[activity_name]
        
        # Assert
        assert "participants" in chess
        assert len(chess["participants"]) == len(expected_participants)
        for participant in expected_participants:
            assert participant in chess["participants"]

    def test_get_activities_contains_metadata(self, client):
        """Test that activities include all required metadata"""
        # Arrange
        activity_name = "Chess Club"
        expected_description = "Learn strategies and compete in chess tournaments"
        expected_schedule = "Fridays, 3:30 PM - 5:00 PM"
        expected_max_participants = 12
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess = data[activity_name]
        
        # Assert
        assert chess["description"] == expected_description
        assert chess["schedule"] == expected_schedule
        assert chess["max_participants"] == expected_max_participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert
        assert response.status_code == 200
        assert f"Signed up {new_email} for {activity_name}" in response.json()["message"]
        
        # Verify participant was added by fetching updated activities
        activities_response = client.get("/activities")
        assert new_email in activities_response.json()[activity_name]["participants"]

    def test_signup_already_registered(self, client):
        """Test that duplicate signups are rejected"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{nonexistent_activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple different students can sign up for same activity"""
        # Arrange
        activity_name = "Chess Club"
        alice_email = "alice@mergington.edu"
        bob_email = "bob@mergington.edu"
        
        # Act
        response1 = client.post(f"/activities/{activity_name}/signup?email={alice_email}")
        response2 = client.post(f"/activities/{activity_name}/signup?email={bob_email}")
        
        # Assert - both signups succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert alice_email in participants
        assert bob_email in participants

    def test_signup_same_student_different_activities(self, client):
        """Test that same student can sign up for different activities"""
        # Arrange
        email = "multitalent@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        
        # Assert - both signups succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data[activity1]["participants"]
        assert email in data[activity2]["participants"]

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with emails containing special characters"""
        # Arrange
        from urllib.parse import quote
        activity_name = "Chess Club"
        email_with_special_chars = "student+plus@mergington.edu"
        
        # Act - use quote to properly URL-encode the email
        encoded_email = quote(email_with_special_chars, safe='')
        response = client.post(f"/activities/{activity_name}/signup?email={encoded_email}")
        
        # Assert
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        assert email_with_special_chars in activities_response.json()[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert f"Removed {email} from {activity_name}" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]

    def test_unregister_not_signed_up(self, client):
        """Test unregistration for student not in activity"""
        # Arrange
        activity_name = "Chess Club"
        unregistered_email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={unregistered_email}")
        
        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]

    def test_unregister_activity_not_found(self, client):
        """Test unregistration from non-existent activity"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{nonexistent_activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_multiple_participants(self, client):
        """Test removing one participant while others remain"""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={email_to_remove}")
        
        # Assert
        assert response.status_code == 200
        
        # Verify only michael was removed and daniel remains
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email_to_remove not in participants
        assert email_to_keep in participants
        assert len(participants) == 1

    def test_unregister_and_resign(self, client):
        """Test unregistering and then re-registering for same activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert unregister succeeded
        assert unregister_response.status_code == 200
        
        # Act - Re-register
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert signup succeeded
        assert signup_response.status_code == 200
        
        # Verify participant is back
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]


class TestRootEndpoint:
    """Tests for root endpoint redirects"""

    def test_root_redirect(self, client):
        """Test that / redirects to /static/index.html"""
        # Arrange
        expected_redirect_location = "/static/index.html"
        expected_status = 307
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert response.headers["location"] == expected_redirect_location

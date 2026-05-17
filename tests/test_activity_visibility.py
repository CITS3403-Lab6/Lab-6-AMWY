from app.models import User


def signup_user(client, username="activityuser", email="activity@example.com"):
    return client.post(
        "/signup",
        data={
            "username": username,
            "email": email,
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )


def test_settings_activity_visibility_dropdown_renders(client):
    signup_user(client)

    response = client.get("/settings")

    assert response.status_code == 200
    assert b'name="activity_visibility"' in response.data
    assert b"Show online status" in response.data
    assert b"Hidden mode" in response.data


def test_activity_visibility_can_be_hidden_and_enabled(client, app):
    signup_user(client)

    hidden_response = client.post(
        "/settings/activity-visibility",
        data={
            "is_public": "on",
            "activity_visibility": "hidden",
        },
        follow_redirects=True,
    )

    assert hidden_response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="activityuser").first()
        assert user is not None
        assert user.show_activity_status is False

    online_response = client.post(
        "/settings/activity-visibility",
        data={
            "is_public": "on",
            "activity_visibility": "online",
        },
        follow_redirects=True,
    )

    assert online_response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="activityuser").first()
        assert user.show_activity_status is True


def test_last_seen_updates_after_request(client, app):
    signup_user(client, "seenuser", "seen@example.com")
    client.get("/dashboard")

    with app.app_context():
        user = User.query.filter_by(username="seenuser").first()
        assert user is not None
        assert hasattr(user, "last_seen_at")
        assert user.last_seen_at is not None

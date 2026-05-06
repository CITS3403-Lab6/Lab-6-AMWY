from app.models import User


def test_signup_creates_user_and_progress(client, app):
    response = client.post(
        "/signup",
        data={
            "username": "authuser",
            "email": "authuser@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="authuser").first()

        assert user is not None
        assert user.email == "authuser@example.com"
        assert user.progress is not None
        assert user.progress.level == 1
        assert user.progress.xp == 0


def test_login_with_correct_password_allows_dashboard_access(client, sample_user):
    login_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert login_response.status_code == 200
    assert b"Dashboard" in login_response.data or b"Your Dashboard" in login_response.data

    dashboard_response = client.get("/dashboard", follow_redirects=True)

    assert dashboard_response.status_code == 200
    assert b"Dashboard" in dashboard_response.data or b"Your Dashboard" in dashboard_response.data


def test_login_with_wrong_password_is_rejected(client, sample_user):
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "wrongpassword",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid" in response.data or b"Login" in response.data


def test_logout_ends_authenticated_session(client, sample_user):
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    logout_response = client.get("/logout", follow_redirects=True)

    assert logout_response.status_code == 200

    dashboard_response = client.get("/dashboard", follow_redirects=True)

    assert dashboard_response.status_code == 200
    assert b"Login" in dashboard_response.data or b"log in" in dashboard_response.data


def test_dashboard_is_protected_for_logged_out_user(client):
    response = client.get("/dashboard", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data or b"log in" in response.data


def test_duplicate_email_signup_is_blocked(client, app):
    client.post(
        "/signup",
        data={
            "username": "firstuser",
            "email": "same@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    client.post(
        "/signup",
        data={
            "username": "seconduser",
            "email": "same@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    with app.app_context():
        users = User.query.filter_by(email="same@example.com").all()
        assert len(users) == 1

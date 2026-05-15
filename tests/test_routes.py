from app.models import User, Task


def test_home_page_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"HabitWise" in response.data


def test_signup_creates_user(client, app):
    response = client.post(
        "/signup",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.check_password("password123")


def test_login_with_valid_user(client, sample_user):
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Dashboard" in response.data or b"Your Dashboard" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data or b"log in" in response.data


def test_add_task_after_login(client, app, sample_user):
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.post(
        "/add-task",
        data={
            "title": "Study for 30 minutes",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        task = Task.query.filter_by(title="Study for 30 minutes").first()
        assert task is not None
        assert task.user_id == sample_user.id

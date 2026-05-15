from app import db
from app.models import User, Progress, Task


def test_duplicate_signup_is_blocked(client, app):
    client.post(
        "/signup",
        data={
            "username": "duplicate",
            "email": "duplicate@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    client.post(
        "/signup",
        data={
            "username": "duplicate",
            "email": "other@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    with app.app_context():
        users = User.query.filter_by(username="duplicate").all()
        assert len(users) == 1


def test_task_requires_title(client, app, sample_user):
    """Test that tasks require a title to be created"""
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
            "title": "",  # Empty title should be rejected by form validation
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        tasks = Task.query.filter_by(title="").all()
        assert len(tasks) == 0


def test_user_cannot_complete_another_users_task(client, app, sample_user):
    with app.app_context():
        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("password123")
        other_progress = Progress(user=other_user)

        db.session.add(other_user)
        db.session.add(other_progress)
        db.session.commit()

        task = Task(
            user_id=other_user.id,
            title="Private task",
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.post(
        f"/complete-task/{task_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        protected_task = db.session.get(Task, task_id)
        assert protected_task.completed is False


def test_private_users_do_not_appear_in_community(client, app, sample_user):
    with app.app_context():
        private_user = User(
            username="privateuser",
            email="private@example.com",
            is_public=False,
        )
        private_user.set_password("password123")
        private_progress = Progress(user=private_user)

        db.session.add(private_user)
        db.session.add(private_progress)
        db.session.commit()

    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    assert b"privateuser" not in response.data


def test_logout_protects_dashboard(client, sample_user):
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    client.get("/logout", follow_redirects=True)

    response = client.get("/dashboard", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data or b"log in" in response.data

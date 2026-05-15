from app import db
from app.models import Progress, Task, User


def login(client):
    return client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )


def test_invalid_task_id_does_not_crash(client, sample_user):
    login(client)

    response = client.post(
        "/complete-task/999999",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Task not found" in response.data or b"Dashboard" in response.data


def test_missing_progress_is_recreated_on_dashboard(client, app, sample_user):
    with app.app_context():
        Progress.query.filter_by(user_id=sample_user.id).delete()
        db.session.commit()

    login(client)

    response = client.get("/dashboard", follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.progress is not None


def test_missing_progress_does_not_break_task_completion(client, app, sample_user):
    with app.app_context():
        Progress.query.filter_by(user_id=sample_user.id).delete()
        task = Task(
            user_id=sample_user.id,
            title="Study with missing progress",
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    login(client)

    response = client.post(
        f"/complete-task/{task_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        task = db.session.get(Task, task_id)

        assert user.progress is not None
        assert task.completed is True
        assert user.progress.xp == 10


def test_user_cannot_complete_another_users_task_error_handled(client, app, sample_user):
    with app.app_context():
        other_user = User(username="other", email="other@example.com")
        other_user.set_password("password123")
        other_progress = Progress(user=other_user)

        db.session.add(other_user)
        db.session.add(other_progress)
        db.session.commit()

        task = Task(
            user_id=other_user.id,
            title="Other user's task",
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    login(client)

    response = client.post(
        f"/complete-task/{task_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"cannot modify" in response.data or b"Dashboard" in response.data

    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task.completed is False


def test_add_task_rejects_empty_title(client, sample_user):
    login(client)

    response = client.post(
        "/add-task",
        data={
            "title": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Task title is required" in response.data or b"Dashboard" in response.data

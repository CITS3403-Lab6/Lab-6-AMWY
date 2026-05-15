from app import db
from app.models import Task, User


def test_complete_task_updates_xp_and_stat(client, app, sample_user):
    task = Task(
        user_id=sample_user.id,
        title="Study for 30 minutes",
    )

    with app.app_context():
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
        user = User.query.filter_by(username="testuser").first()
        completed_task = db.session.get(Task, task_id)

        assert completed_task.completed is True
        assert user.progress.xp == 10

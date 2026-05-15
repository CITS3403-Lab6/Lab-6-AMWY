from datetime import date

from app import db
from app.models import Challenge, Task, User


def signup_user(client, username, email):
    return client.post(
        "/signup",
        data={
            "username": username,
            "email": email,
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )


def test_evaluate_day_reduces_hp_when_target_is_missed(client, app):
    signup_user(client, "evalmiss", "evalmiss@example.com")

    response = client.post("/evaluate-day", follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="evalmiss").first()
        assert user is not None
        assert user.progress is not None
        # Default Sage mindset requires 50% completion, with 0 tasks, 0% completion, so lose 50 HP
        assert user.progress.hp == 50
        assert user.progress.streak == 0
        assert user.progress.last_evaluated_date == date.today()


def test_evaluate_day_only_applies_once_per_day(client, app):
    signup_user(client, "evalonce", "evalonce@example.com")

    first_response = client.post("/evaluate-day", follow_redirects=True)
    second_response = client.post("/evaluate-day", follow_redirects=True)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="evalonce").first()
        # Default Sage mindset requires 50% completion, with 0 tasks, 0% completion, so lose 50 HP
        assert user.progress.hp == 50
        assert user.progress.last_evaluated_date == date.today()


def test_evaluate_day_increases_streak_when_target_is_met(client, app):
    signup_user(client, "evalpass", "evalpass@example.com")

    with app.app_context():
        user = User.query.filter_by(username="evalpass").first()

        challenge = Challenge(
                        user_id=user.id,
            mindset_type="Sage",
        )

        task = Task(
            user_id=user.id,
            title="Study for 30 minutes",
            completed=True,
            task_date=date.today(),
        )

        db.session.add(challenge)
        db.session.add(task)
        db.session.commit()

    response = client.post("/evaluate-day", follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="evalpass").first()
        # Sage requires 50% completion, with 1 task and 1 completed, 100% > 50%, so no HP loss
        user = User.query.filter_by(username="evalpass").first()
        assert user.progress.hp == 100
        assert user.progress.streak == 1
        assert user.progress.last_evaluated_date == date.today()

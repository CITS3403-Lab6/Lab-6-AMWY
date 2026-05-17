from datetime import date

from app import db
from app.models import Challenge, Progress, Task, User
from app.services import DEFAULT_STARTER_TASKS, seed_default_tasks_for_user
from init_db import DEMO_PASSWORD, DEMO_USERS, seed_demo_data


def test_seed_default_tasks_for_user_creates_eight_tasks(app):
    with app.app_context():
        user = User(username="starter_user", email="starter@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        created_tasks = seed_default_tasks_for_user(
            user,
            task_date=date.today(),
            skip_when_testing=False,
        )

        assert len(created_tasks) == len(DEFAULT_STARTER_TASKS)
        assert len(created_tasks) == 8

        saved_tasks = Task.query.filter_by(user_id=user.id).all()

        assert len(saved_tasks) == 8
        assert {task.stat_category for task in saved_tasks} <= {"STR", "INT", "SPI", "VIT", "CHA"}


def test_seed_default_tasks_for_user_is_idempotent(app):
    with app.app_context():
        user = User(username="idempotent_user", email="idempotent@example.com")
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        first = seed_default_tasks_for_user(user, skip_when_testing=False)
        second = seed_default_tasks_for_user(user, skip_when_testing=False)

        assert len(first) == 8
        assert second == []
        assert Task.query.filter_by(user_id=user.id).count() == 8


def test_demo_seed_data_creates_realistic_public_and_private_users(app):
    with app.app_context():
        users = seed_demo_data(reset_database=True)

        assert len(users) >= 5

        public_users = User.query.filter_by(is_public=True).all()
        private_users = User.query.filter_by(is_public=False).all()

        assert len(public_users) >= 3
        assert len(private_users) >= 1

        emails = {user.email for user in users}

        assert "demo_public@example.com" in emails
        assert "demo_private@example.com" in emails

        primary_user = User.query.filter_by(username="demo_public").first()

        assert primary_user is not None
        assert primary_user.check_password(DEMO_PASSWORD)


def test_demo_seed_data_creates_progress_tasks_and_challenges(app):
    with app.app_context():
        seed_demo_data(reset_database=True)

        for user_data in DEMO_USERS:
            user = User.query.filter_by(username=user_data["username"]).first()

            assert user is not None

            progress = Progress.query.filter_by(user_id=user.id).first()
            tasks = Task.query.filter_by(user_id=user.id).all()
            challenge = Challenge.query.filter_by(user_id=user.id).first()

            assert progress is not None
            assert tasks
            assert challenge is not None
            assert progress.level >= 1
            assert progress.xp >= 0
            assert progress.streak >= 0

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.constants import TASK_XP_REWARD
from app.models import Challenge, Progress, Reflection, Task, User
from app.services import calculate_level_from_xp, complete_user_task


def test_user_cascade_deletes_related_records(app):
    user = User(username="cascadeuser", email="cascade@example.com")
    user.set_password("password123")

    progress = Progress(user=user)
    task = Task(user=user, title="Study")
    challenge = Challenge(
        user=user,
        mindset_type="Sage",
    )
    reflection = Reflection(user=user, mood="good", note="Test note")

    db.session.add_all([user, progress, task, challenge, reflection])
    db.session.commit()

    user_id = user.id

    db.session.delete(user)
    db.session.commit()

    assert Progress.query.filter_by(user_id=user_id).first() is None
    assert Task.query.filter_by(user_id=user_id).first() is None
    assert Challenge.query.filter_by(user_id=user_id).first() is None
    assert Reflection.query.filter_by(user_id=user_id).first() is None


def test_progress_is_one_to_one_with_user(app, sample_user):
    duplicate_progress = Progress(user_id=sample_user.id)

    db.session.add(duplicate_progress)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_invalid_mindset_type_fails_database_constraint(app, sample_user):
    challenge = Challenge(
        user_id=sample_user.id,
        mindset_type="Invalid",
    )

    db.session.add(challenge)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_latest_challenge_returns_newest_challenge(app, sample_user):
    older = Challenge(
        user_id=sample_user.id,
        mindset_type="Sage",
    )

    newer = Challenge(
        user_id=sample_user.id,
        mindset_type="Warrior",
    )

    db.session.add_all([older, newer])
    db.session.commit()

    latest = sample_user.latest_challenge()

    assert latest is not None
    assert latest.mindset_type == "Warrior"


def test_calculate_level_from_xp():
    assert calculate_level_from_xp(0) == 1
    assert calculate_level_from_xp(99) == 1
    assert calculate_level_from_xp(100) == 2
    assert calculate_level_from_xp(199) == 2
    assert calculate_level_from_xp(200) == 3


def test_completing_task_does_not_award_xp_twice(app, sample_user):
    task = Task(
        user_id=sample_user.id,
        title="Study once",
    )

    db.session.add(task)
    db.session.commit()

    completed_now, levelled_up = complete_user_task(sample_user, task)
    completed_again, levelled_up_again = complete_user_task(sample_user, task)

    assert completed_now is True
    assert levelled_up is False
    assert completed_again is False
    assert levelled_up_again is False
    assert sample_user.progress.xp == TASK_XP_REWARD


def test_task_completion_can_level_user_up(app, sample_user):
    sample_user.progress.xp = 90
    sample_user.progress.level = 1

    task = Task(
        user_id=sample_user.id,
        title="Level up task",
    )

    db.session.add(task)
    db.session.commit()

    completed_now, levelled_up = complete_user_task(sample_user, task)

    assert completed_now is True
    assert levelled_up is True
    assert sample_user.progress.xp == 100
    assert sample_user.progress.level == 2


@pytest.mark.parametrize(
    "category,field_name",
    [
        ("Sage", "mindset_type"),
        ("Warrior", "mindset_type"),
        ("Demon", "mindset_type"),
    ],
)
def test_challenge_mindset_types(app, sample_user, category, field_name):
    challenge = Challenge(
        user_id=sample_user.id,
        mindset_type=category,
    )

    db.session.add(challenge)
    db.session.commit()

    assert getattr(challenge, field_name) == category


def test_dashboard_challenge_save_flow(client, app, sample_user):
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.post(
        "/dashboard",
        data={
            "mindset_type": "Warrior",
            "is_public": "y",
            "save_challenge": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        challenge = user.latest_challenge()

        assert challenge is not None
        assert challenge.mindset_type == "Warrior"
        assert user.is_public is True


def test_invalid_mindset_type_submission_is_rejected(client, app, sample_user):
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    response = client.post(
        "/dashboard",
        data={
            "mindset_type": "Invalid",
            "save_challenge": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        challenge = Challenge.query.filter_by(user_id=sample_user.id).first()
        assert challenge is None

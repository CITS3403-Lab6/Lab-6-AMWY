from app import db
from app.models import User, Progress, Task, Challenge, Reflection


def test_user_password_hashing(app):
    user = User(username="advay", email="advay@example.com")
    user.set_password("secret123")

    assert user.password_hash != "secret123"
    assert user.check_password("secret123")
    assert not user.check_password("wrongpassword")


def test_user_progress_relationship(app):
    user = User(username="michael", email="michael@example.com")
    user.set_password("password123")
    progress = Progress(user=user)

    db.session.add(user)
    db.session.add(progress)
    db.session.commit()

    saved_user = User.query.filter_by(username="michael").first()

    assert saved_user is not None
    assert saved_user.progress is not None
    assert saved_user.progress.level == 1
    assert saved_user.progress.xp == 0


def test_task_creation(app, sample_user):
    task = Task(
        user_id=sample_user.id,
        title="Study for 30 minutes",
        stat_category="INT",
    )

    db.session.add(task)
    db.session.commit()

    saved_task = Task.query.filter_by(title="Study for 30 minutes").first()

    assert saved_task is not None
    assert saved_task.user_id == sample_user.id
    assert saved_task.completed is False


def test_challenge_creation(app, sample_user):
    challenge = Challenge(
        user_id=sample_user.id,
        challenge_type="study",
        difficulty="easy",
        mindset_type="Sage",
    )

    db.session.add(challenge)
    db.session.commit()

    saved_challenge = Challenge.query.filter_by(user_id=sample_user.id).first()

    assert saved_challenge is not None
    assert saved_challenge.challenge_type == "study"
    assert saved_challenge.mindset_type == "Sage"


def test_reflection_creation(app, sample_user):
    reflection = Reflection(
        user_id=sample_user.id,
        mood="good",
        note="Felt productive today.",
    )

    db.session.add(reflection)
    db.session.commit()

    saved_reflection = Reflection.query.filter_by(user_id=sample_user.id).first()

    assert saved_reflection is not None
    assert saved_reflection.note == "Felt productive today."

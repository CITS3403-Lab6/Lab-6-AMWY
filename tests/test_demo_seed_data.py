from app.models import Challenge, Progress, Task, User
from init_db import DEMO_PASSWORD, seed_demo_data


def test_demo_seed_data_creates_public_and_private_users(app):
    with app.app_context():
        seed_demo_data()

        public_user = User.query.filter_by(username="demo_public").first()
        private_user = User.query.filter_by(username="demo_private").first()

        assert public_user is not None
        assert private_user is not None

        assert public_user.email == "demo_public@example.com"
        assert private_user.email == "demo_private@example.com"

        assert public_user.check_password(DEMO_PASSWORD)
        assert private_user.check_password(DEMO_PASSWORD)

        if hasattr(public_user, "is_public"):
            assert public_user.is_public is True

        if hasattr(private_user, "is_public"):
            assert private_user.is_public is False


def test_demo_seed_data_creates_progress_tasks_and_challenges(app):
    with app.app_context():
        seed_demo_data()

        demo_public = User.query.filter_by(username="demo_public").first()

        assert demo_public is not None

        progress = Progress.query.filter_by(user_id=demo_public.id).first()
        tasks = Task.query.filter_by(user_id=demo_public.id).all()
        challenge = Challenge.query.filter_by(user_id=demo_public.id).first()

        assert progress is not None
        assert tasks
        assert challenge is not None

        if hasattr(progress, "hp"):
            assert progress.hp > 0

        if hasattr(progress, "xp"):
            assert progress.xp >= 0

        if hasattr(progress, "level"):
            assert progress.level >= 1

        if hasattr(progress, "streak"):
            assert progress.streak >= 0

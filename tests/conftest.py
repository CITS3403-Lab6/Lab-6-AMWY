import pytest

from app import create_app, db
from app.models import User, Progress


@pytest.fixture()
def app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_user(app):
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")

    progress = Progress(user=user)

    db.session.add(user)
    db.session.add(progress)
    db.session.commit()

    return user

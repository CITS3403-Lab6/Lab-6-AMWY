from app import db
from app.models import Progress, User


def login(client):
    return client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )


def test_public_user_appears_in_community(client, sample_user):
    sample_user.is_public = True
    db.session.commit()

    login(client)

    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    assert b"testuser" in response.data


def test_private_user_does_not_appear_in_community(client, app, sample_user):
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

    login(client)

    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    assert b"privateuser" not in response.data


def test_current_user_hidden_when_profile_is_private(client, app, sample_user):
    with app.app_context():
        sample_user.is_public = False
        db.session.commit()

    login(client)

    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    assert b"The public leaderboard is empty" in response.data


def test_community_requires_login(client):
    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data or b"log in" in response.data

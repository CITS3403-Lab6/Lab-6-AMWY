from app.models import User


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


def test_settings_page_loads_for_logged_in_user(client):
    response = signup_user(client, "settingsuser", "settingsuser@example.com")

    assert response.status_code == 200

    response = client.get("/settings")

    assert response.status_code == 200
    assert b"Settings" in response.data
    assert b"Privacy Settings" in response.data


def test_settings_page_is_protected_for_logged_out_user(client):
    response = client.get("/settings", follow_redirects=False)

    assert response.status_code in (302, 401)


def test_user_can_make_profile_private_from_settings(client, app):
    signup_user(client, "privateuser", "privateuser@example.com")

    response = client.post(
        "/settings",
        data={"privacy": "private"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"private" in response.data.lower()

    with app.app_context():
        user = User.query.filter_by(username="privateuser").first()
        assert user is not None
        assert user.is_public is False


def test_user_can_make_profile_public_from_settings(client, app):
    signup_user(client, "publicuser", "publicuser@example.com")

    client.post(
        "/settings",
        data={"privacy": "private"},
        follow_redirects=True,
    )

    response = client.post(
        "/settings",
        data={"privacy": "public"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"public" in response.data.lower()

    with app.app_context():
        user = User.query.filter_by(username="publicuser").first()
        assert user is not None
        assert user.is_public is True


def test_settings_accepts_checkbox_style_public_value(client, app):
    signup_user(client, "checkboxuser", "checkboxuser@example.com")

    response = client.post(
        "/settings",
        data={"is_public": "on"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="checkboxuser").first()
        assert user.is_public is True


def test_private_user_hidden_from_community_after_settings_update(client, app):
    signup_user(client, "hiddenuser", "hiddenuser@example.com")

    client.post(
        "/settings",
        data={"privacy": "private"},
        follow_redirects=True,
    )

    response = client.get("/community")

    assert response.status_code == 200
    assert b"The public leaderboard is empty" in response.data or b"hiddenuser" not in response.data

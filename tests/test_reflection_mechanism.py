from app.models import Reflection


def login(client):
    return client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )


def test_reflection_saves_valid_note(client, app, sample_user):
    login(client)

    response = client.post(
        "/reflection",
        data={
            "mood": "good",
            "note": "I stayed consistent today.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        reflection = Reflection.query.filter_by(user_id=sample_user.id).first()
        assert reflection is not None
        assert reflection.mood == "good"
        assert reflection.note == "I stayed consistent today."


def test_blank_reflection_note_is_allowed(client, app, sample_user):
    login(client)

    response = client.post(
        "/reflection",
        data={
            "mood": "okay",
            "note": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        reflection = Reflection.query.filter_by(user_id=sample_user.id).first()
        assert reflection is not None
        assert reflection.note == ""


def test_multiple_reflections_can_be_saved(client, app, sample_user):
    login(client)

    client.post(
        "/reflection",
        data={
            "mood": "good",
            "note": "First reflection.",
        },
        follow_redirects=True,
    )

    client.post(
        "/reflection",
        data={
            "mood": "great",
            "note": "Second reflection.",
        },
        follow_redirects=True,
    )

    with app.app_context():
        reflections = Reflection.query.filter_by(user_id=sample_user.id).all()
        assert len(reflections) == 2


def test_overlong_reflection_is_rejected(client, app, sample_user):
    login(client)

    long_note = "x" * 1001

    response = client.post(
        "/reflection",
        data={
            "mood": "good",
            "note": long_note,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        reflection = Reflection.query.filter_by(user_id=sample_user.id).first()
        assert reflection is None

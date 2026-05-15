from app import db
from app.models import AccountabilityPartner, Challenge, Progress, User


def create_user(username, email, is_public=True, level=1, xp=0, streak=0, hp=100):
    user = User(username=username, email=email, is_public=is_public)
    user.set_password("password123")

    progress = Progress(
        user=user,
        level=level,
        xp=xp,
        streak=streak,
        hp=hp,
        max_hp=100,
    )

    db.session.add(user)
    db.session.add(progress)
    db.session.commit()

    return user


def login(client, username):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": "password123",
        },
        follow_redirects=True,
    )


def test_user_can_add_public_accountability_partner(client, app):
    with app.app_context():
        owner = create_user("owneruser", "owner@example.com", is_public=True)
        partner = create_user("partneruser", "partner@example.com", is_public=True)

    login(client, "owneruser")

    response = client.post(
        "/community/add-partner",
        data={"partner_identifier": "partneruser"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"partneruser" in response.data

    with app.app_context():
        owner = User.query.filter_by(username="owneruser").first()
        partner = User.query.filter_by(username="partneruser").first()

        link = AccountabilityPartner.query.filter_by(
            user_id=owner.id,
            partner_id=partner.id,
        ).first()

        assert link is not None


def test_user_can_add_partner_by_email(client, app):
    with app.app_context():
        create_user("emailowner", "emailowner@example.com", is_public=True)
        partner = create_user("emailpartner", "emailpartner@example.com", is_public=True)

    login(client, "emailowner")

    response = client.post(
        "/community/add-partner",
        data={"partner_identifier": "emailpartner@example.com"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"emailpartner" in response.data


def test_user_cannot_add_private_user_as_partner(client, app):
    with app.app_context():
        create_user("publicowner", "publicowner@example.com", is_public=True)
        create_user("privatepartner", "privatepartner@example.com", is_public=False)

    login(client, "publicowner")

    response = client.post(
        "/community/add-partner",
        data={"partner_identifier": "privatepartner"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert AccountabilityPartner.query.count() == 0


def test_user_cannot_add_self_as_partner(client, app):
    with app.app_context():
        create_user("selfuser", "self@example.com", is_public=True)

    login(client, "selfuser")

    response = client.post(
        "/community/add-partner",
        data={"partner_identifier": "selfuser"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert AccountabilityPartner.query.count() == 0


def test_duplicate_partner_is_not_added_twice(client, app):
    with app.app_context():
        owner = create_user("dupowner", "dupowner@example.com", is_public=True)
        partner = create_user("duppartner", "duppartner@example.com", is_public=True)

    login(client, "dupowner")

    client.post(
        "/community/add-partner",
        data={"partner_identifier": "duppartner"},
        follow_redirects=True,
    )

    client.post(
        "/community/add-partner",
        data={"partner_identifier": "duppartner"},
        follow_redirects=True,
    )

    with app.app_context():
        owner = User.query.filter_by(username="dupowner").first()
        partner = User.query.filter_by(username="duppartner").first()

        count = AccountabilityPartner.query.filter_by(
            user_id=owner.id,
            partner_id=partner.id,
        ).count()

        assert count == 1


def test_community_page_shows_partner_stats_and_goal(client, app):
    with app.app_context():
        owner = create_user("statsowner", "statsowner@example.com", is_public=True)
        partner = create_user(
            "statspartner",
            "statspartner@example.com",
            is_public=True,
            level=7,
            xp=650,
            streak=4,
            hp=88,
        )

        challenge = Challenge(
            user_id=partner.id,
            mindset_type="Sage",
        )

        db.session.add(challenge)
        db.session.commit()

    login(client, "statsowner")

    response = client.post(
        "/community/add-partner",
        data={"partner_identifier": "statspartner"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"statspartner" in response.data
    assert b"Circle Score" in response.data or b"Level" in response.data
    # Check for mindset type displayed on community page
    assert b"Sage" in response.data or b"sage" in response.data.lower()


def test_user_can_remove_accountability_partner(client, app):
    with app.app_context():
        owner = create_user("removeowner", "removeowner@example.com", is_public=True)
        partner = create_user("removepartner", "removepartner@example.com", is_public=True)

        partner_id = partner.id

        link = AccountabilityPartner(user_id=owner.id, partner_id=partner_id)
        db.session.add(link)
        db.session.commit()

    login(client, "removeowner")

    response = client.post(
        f"/community/remove-partner/{partner_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert AccountabilityPartner.query.count() == 0


def test_add_partner_route_accepts_frontend_flexible_field_names(client, app):
    with app.app_context():
        owner = create_user("flexowner", "flexowner@example.com", is_public=True)
        partner = create_user("flexpartner", "flexpartner@example.com", is_public=True)

    login(client, "flexowner")

    response = client.post(
        "/community/partners/add",
        data={"username": "flexpartner"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"flexpartner" in response.data

    with app.app_context():
        owner = User.query.filter_by(username="flexowner").first()
        partner = User.query.filter_by(username="flexpartner").first()

        link = AccountabilityPartner.query.filter_by(
            user_id=owner.id,
            partner_id=partner.id,
        ).first()

        assert link is not None


def test_remove_partner_route_accepts_frontend_flexible_url(client, app):
    with app.app_context():
        owner = create_user("flexremoveowner", "flexremoveowner@example.com", is_public=True)
        partner = create_user("flexremovepartner", "flexremovepartner@example.com", is_public=True)
        partner_id = partner.id

        link = AccountabilityPartner(user_id=owner.id, partner_id=partner_id)
        db.session.add(link)
        db.session.commit()

    login(client, "flexremoveowner")

    response = client.post(
        f"/community/partners/{partner_id}/remove",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        assert AccountabilityPartner.query.count() == 0

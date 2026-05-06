from app import db
from app.models import User


def test_password_is_never_stored_as_plain_text(app):
    user = User(username="secureuser", email="secure@example.com")
    user.set_password("supersecret123")

    db.session.add(user)
    db.session.commit()

    saved_user = User.query.filter_by(username="secureuser").first()

    assert saved_user is not None
    assert saved_user.password_hash != "supersecret123"
    assert "supersecret123" not in saved_user.password_hash


def test_password_hash_verifies_correct_password(app):
    user = User(username="verifyuser", email="verify@example.com")
    user.set_password("password123")

    db.session.add(user)
    db.session.commit()

    saved_user = User.query.filter_by(username="verifyuser").first()

    assert saved_user.check_password("password123") is True


def test_password_hash_rejects_wrong_password(app):
    user = User(username="rejectuser", email="reject@example.com")
    user.set_password("password123")

    db.session.add(user)
    db.session.commit()

    saved_user = User.query.filter_by(username="rejectuser").first()

    assert saved_user.check_password("wrongpassword") is False


def test_two_users_with_same_password_have_different_hashes(app):
    user_one = User(username="userone", email="one@example.com")
    user_two = User(username="usertwo", email="two@example.com")

    user_one.set_password("samepassword123")
    user_two.set_password("samepassword123")

    db.session.add(user_one)
    db.session.add(user_two)
    db.session.commit()

    assert user_one.password_hash != user_two.password_hash

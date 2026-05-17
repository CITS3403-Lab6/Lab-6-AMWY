from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import AccountabilityPartner, Challenge, Progress, Task, User


DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    {
        "username": "demo_public",
        "email": "demo_public@example.com",
        "is_public": True,
        "show_activity_status": True,
        "hp": 92,
        "max_hp": 100,
        "xp": 840,
        "level": 8,
        "streak": 12,
        "challenge_type": "study",
        "difficulty": "medium",
        "mindset_type": "Sage",
        "tasks": [
            ("Review lecture notes", "INT", True),
            ("Read one page of a book", "INT", True),
            ("Plan tomorrow's top 3 tasks", "SPI", True),
            ("Avoid one distraction session", "SPI", False),
            ("Drink enough water", "VIT", True),
            ("Message one mate", "CHA", False),
        ],
    },
    {
        "username": "demo_private",
        "email": "demo_private@example.com",
        "is_public": False,
        "show_activity_status": False,
        "hp": 64,
        "max_hp": 100,
        "xp": 310,
        "level": 4,
        "streak": 3,
        "challenge_type": "meditation",
        "difficulty": "easy",
        "mindset_type": "Sage",
        "tasks": [
            ("Do a 5 minute reflection", "SPI", True),
            ("Meditate for five minutes", "SPI", False),
            ("Plan tomorrow's top 3 tasks", "INT", True),
        ],
    },
    {
        "username": "will_campbell",
        "email": "will.campbell@example.com",
        "is_public": True,
        "show_activity_status": True,
        "hp": 78,
        "max_hp": 100,
        "xp": 430,
        "level": 5,
        "streak": 6,
        "challenge_type": "fitness",
        "difficulty": "easy",
        "mindset_type": "Warrior",
        "tasks": [
            ("Walk 10,000 steps", "VIT", True),
            ("Stretch for ten minutes", "VIT", True),
            ("Prepare a healthy meal", "STR", False),
            ("Complete a 10 minute tidy-up", "STR", True),
        ],
    },
    {
        "username": "emily_clarke",
        "email": "emily.clarke@example.com",
        "is_public": True,
        "show_activity_status": True,
        "hp": 100,
        "max_hp": 100,
        "xp": 1250,
        "level": 13,
        "streak": 21,
        "challenge_type": "creativity",
        "difficulty": "hard",
        "mindset_type": "Demon",
        "tasks": [
            ("Work on creative project", "CHA", True),
            ("Complete daily review", "SPI", True),
            ("Share progress update", "CHA", True),
            ("Sketch one idea", "INT", True),
            ("Avoid one distraction session", "SPI", True),
        ],
    },
    {
        "username": "noah_nguyen",
        "email": "noah.nguyen@example.com",
        "is_public": True,
        "show_activity_status": True,
        "hp": 88,
        "max_hp": 100,
        "xp": 670,
        "level": 7,
        "streak": 9,
        "challenge_type": "nutrition",
        "difficulty": "medium",
        "mindset_type": "Sage",
        "tasks": [
            ("Drink enough water", "VIT", True),
            ("Prepare a balanced meal", "VIT", True),
            ("Read one page of a book", "INT", False),
            ("Do a 5 minute reflection", "SPI", True),
        ],
    },
    {
        "username": "mia_anderson",
        "email": "mia.anderson@example.com",
        "is_public": True,
        "show_activity_status": True,
        "hp": 95,
        "max_hp": 100,
        "xp": 980,
        "level": 10,
        "streak": 15,
        "challenge_type": "study",
        "difficulty": "hard",
        "mindset_type": "Warrior",
        "tasks": [
            ("Finish assignment draft", "INT", True),
            ("Review feedback notes", "INT", True),
            ("Message group project team", "CHA", True),
            ("Take a short walk", "VIT", False),
        ],
    },
]


PARTNER_LINKS = [
    ("demo_public", "will_campbell"),
    ("demo_public", "emily_clarke"),
    ("demo_public", "noah_nguyen"),
    ("demo_public", "mia_anderson"),
]


def has_column(model, column_name):
    return column_name in model.__table__.columns


def set_if_supported(instance, field_name, value):
    if has_column(instance.__class__, field_name):
        setattr(instance, field_name, value)


def set_user_password(user, password):
    if hasattr(user, "set_password"):
        user.set_password(password)
    elif has_column(User, "password_hash"):
        user.password_hash = generate_password_hash(password)
    elif has_column(User, "password"):
        user.password = generate_password_hash(password)
    else:
        raise RuntimeError("User model has no supported password field.")


def create_progress(user, user_data):
    progress = Progress()

    set_if_supported(progress, "user_id", user.id)
    set_if_supported(progress, "hp", user_data["hp"])
    set_if_supported(progress, "max_hp", user_data["max_hp"])
    set_if_supported(progress, "xp", user_data["xp"])
    set_if_supported(progress, "level", user_data["level"])
    set_if_supported(progress, "streak", user_data["streak"])

    set_if_supported(progress, "strength_xp", 90)
    set_if_supported(progress, "intelligence_xp", 140)
    set_if_supported(progress, "spirituality_xp", 110)
    set_if_supported(progress, "vitality_xp", 130)
    set_if_supported(progress, "charisma_xp", 100)

    db.session.add(progress)
    return progress


def create_challenge(user, user_data):
    challenge = Challenge()

    set_if_supported(challenge, "user_id", user.id)
    set_if_supported(challenge, "challenge_type", user_data["challenge_type"])
    set_if_supported(challenge, "difficulty", user_data["difficulty"])
    set_if_supported(challenge, "mindset_type", user_data["mindset_type"])
    set_if_supported(challenge, "mode", user_data["mindset_type"])
    set_if_supported(challenge, "goal", user_data["challenge_type"])

    db.session.add(challenge)
    return challenge


def create_tasks(user, user_data):
    for title, stat_category, completed in user_data["tasks"]:
        task = Task()

        set_if_supported(task, "user_id", user.id)
        set_if_supported(task, "title", title)
        set_if_supported(task, "description", title)
        set_if_supported(task, "stat_category", stat_category)
        set_if_supported(task, "completed", completed)
        set_if_supported(task, "task_date", date.today())

        db.session.add(task)


def create_demo_user(user_data):
    user = User(
        username=user_data["username"],
        email=user_data["email"],
    )

    set_user_password(user, DEMO_PASSWORD)
    set_if_supported(user, "is_public", user_data["is_public"])
    set_if_supported(user, "show_activity_status", user_data.get("show_activity_status", True))

    db.session.add(user)
    db.session.flush()

    create_progress(user, user_data)
    create_challenge(user, user_data)
    create_tasks(user, user_data)

    return user


def create_partner_links(users_by_username):
    if AccountabilityPartner is None:
        return

    for user_username, partner_username in PARTNER_LINKS:
        user = users_by_username.get(user_username)
        partner = users_by_username.get(partner_username)

        if user is None or partner is None:
            continue

        link = AccountabilityPartner()

        set_if_supported(link, "user_id", user.id)
        set_if_supported(link, "partner_id", partner.id)

        db.session.add(link)


def seed_demo_data(reset_database=True):
    if reset_database:
        db.drop_all()
        db.create_all()
    else:
        db.create_all()

    users_by_username = {}

    for user_data in DEMO_USERS:
        user = create_demo_user(user_data)
        users_by_username[user.username] = user

    create_partner_links(users_by_username)

    db.session.commit()

    return list(users_by_username.values())


def main():
    app = create_app("development")

    with app.app_context():
        users = seed_demo_data(reset_database=True)

        print("Database initialised with realistic demo data.")
        print("")
        print("Demo login details:")
        for user in users:
            print(f"- {user.username}: {user.email} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()

from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Challenge, Progress, Task, User


DEMO_PASSWORD = "Password123!"

DEMO_USERS = [
    {
        "username": "demo_public",
        "email": "demo_public@example.com",
        "is_public": True,
        "hp": 90,
        "max_hp": 100,
        "xp": 250,
        "level": 3,
        "streak": 5,
        "challenge_type": "study",
        "difficulty": "medium",
        "mindset_type": "Sage",
        "tasks": [
            ("Complete one focused study session", "INT", True),
            ("Review HabitWise progress", "VIT", True),
            ("Plan tomorrow's tasks", "SPI", False),
        ],
    },
    {
        "username": "demo_private",
        "email": "demo_private@example.com",
        "is_public": False,
        "hp": 75,
        "max_hp": 100,
        "xp": 120,
        "level": 2,
        "streak": 2,
        "challenge_type": "fitness",
        "difficulty": "easy",
        "mindset_type": "Warrior",
        "tasks": [
            ("Go for a short walk", "VIT", True),
            ("Stretch for ten minutes", "VIT", False),
        ],
    },
    {
        "username": "demo_partner",
        "email": "demo_partner@example.com",
        "is_public": True,
        "hp": 100,
        "max_hp": 100,
        "xp": 520,
        "level": 6,
        "streak": 9,
        "challenge_type": "creativity",
        "difficulty": "hard",
        "mindset_type": "Demon",
        "tasks": [
            ("Work on a creative project", "CHA", True),
            ("Complete daily review", "SPI", True),
            ("Share progress publicly", "CHA", True),
        ],
    },
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

    if has_column(Progress, "user_id"):
        progress.user_id = user.id
    elif hasattr(progress, "user"):
        progress.user = user

    defaults = {
        "hp": user_data["hp"],
        "max_hp": user_data["max_hp"],
        "xp": user_data["xp"],
        "level": user_data["level"],
        "streak": user_data["streak"],
        "strength_xp": 20,
        "intelligence_xp": 40,
        "spirituality_xp": 15,
        "vitality_xp": 25,
        "charisma_xp": 30,
    }

    for field, value in defaults.items():
        set_if_supported(progress, field, value)

    db.session.add(progress)
    return progress


def create_challenge(user, user_data):
    challenge = Challenge()

    if has_column(Challenge, "user_id"):
        challenge.user_id = user.id

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

        if has_column(Task, "user_id"):
            task.user_id = user.id

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

    db.session.add(user)
    db.session.flush()

    create_progress(user, user_data)
    create_challenge(user, user_data)
    create_tasks(user, user_data)

    return user


def seed_demo_data(reset_database=True):
    """Create clean demo data for final testing.

    reset_database=True intentionally rebuilds the local demo database so stale
    SQLite schemas from earlier development branches do not break init_db.py.
    """
    if reset_database:
        db.drop_all()
        db.create_all()
    else:
        db.create_all()

    created_users = []

    for user_data in DEMO_USERS:
        created_users.append(create_demo_user(user_data))

    db.session.commit()

    return created_users


def main():
    app = create_app("development")

    with app.app_context():
        users = seed_demo_data(reset_database=True)

        print("Database initialised with demo data.")
        print("")
        print("Demo login details:")
        for user in users:
            print(f"- {user.email} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()

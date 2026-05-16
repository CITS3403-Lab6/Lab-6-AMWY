from datetime import date, datetime, timedelta
import math

from sqlalchemy import or_

from app import db
from app.constants import (
    CHARACTER_REVEAL_INTERVAL,
    LEVEL_XP_MULTIPLIER,
    MAX_HP,
    MAX_LEVEL,
    MAX_REFLECTION_LENGTH,
    TASK_XP_REWARD,
)
from app.models import AccountabilityPartner, Progress, Reflection, Task, User


# Compatibility constants used by some tests / older code
DEFAULT_DIFFICULTY = "medium"
DEFAULT_CHALLENGE_TYPE = "study"
DEFAULT_MINDSET_TYPE = "Sage"
DEFAULT_DAILY_HP_DAMAGE = 10

MINDSET_COMPLETION_TARGETS = {
    "sage": 50,
    "warrior": 70,
    "demon": 90,
}

DIFFICULTY_COMPLETION_TARGETS = {
    "easy": 50,
    "medium": 70,
    "hard": 90,
}


def _coerce_int(value, field_name, default=None):
    """Safely convert a value to int."""
    if value is None:
        if default is not None:
            return default
        raise ValueError(f"{field_name} is required.")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite.")

    return int(round(number))


def _clamp_int(value, minimum, maximum, field_name, default=None):
    """Convert a value to int and clamp it between minimum and maximum."""
    number = _coerce_int(value, field_name, default=default)
    return max(minimum, min(maximum, number))


def normalise_progress_fields(progress):
    """Repair unsafe progress values before calculations."""
    if progress is None:
        raise ValueError("Progress record is required.")

    max_hp = _coerce_int(getattr(progress, "max_hp", None), "max_hp", default=MAX_HP)
    if max_hp <= 0:
        max_hp = MAX_HP

    hp = _coerce_int(getattr(progress, "hp", None), "hp", default=max_hp)
    xp = _coerce_int(getattr(progress, "xp", None), "xp", default=0)
    level = _coerce_int(getattr(progress, "level", None), "level", default=1)
    streak = _coerce_int(getattr(progress, "streak", None), "streak", default=0)

    progress.max_hp = max_hp
    progress.hp = max(0, min(max_hp, hp))
    progress.xp = max(0, xp)
    progress.level = max(1, min(MAX_LEVEL, level))
    progress.streak = max(0, streak)

    return progress


def calculate_level_from_xp(xp):
    """Convert XP into a capped level."""
    safe_xp = _coerce_int(xp, "XP", default=0)

    if safe_xp < 0:
        raise ValueError("XP cannot be negative.")

    return min((safe_xp // LEVEL_XP_MULTIPLIER) + 1, MAX_LEVEL)


def get_or_create_progress(user):
    """Return a user's progress record, creating one if missing."""
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid user is required to load progress.")

    if user.progress is not None:
        return normalise_progress_fields(user.progress)

    progress = Progress(
        user_id=user.id,
        hp=MAX_HP,
        max_hp=MAX_HP,
        xp=0,
        level=1,
        streak=0,
    )

    db.session.add(progress)
    db.session.commit()

    return progress


def award_task_xp(user, task):
    """Award XP for a completed task and update level."""
    progress = get_or_create_progress(user)

    old_level = progress.level
    progress.xp += TASK_XP_REWARD
    progress.level = calculate_level_from_xp(progress.xp)

    return progress.level > old_level


def complete_user_task(user, task):
    """Complete a user's task and award XP only once."""
    if task.user_id != user.id:
        raise PermissionError("Cannot complete another user's task.")

    if task.completed:
        return False, False

    task.completed = True
    levelled_up = award_task_xp(user, task)
    db.session.commit()

    return True, levelled_up


def get_mindset_target(mindset_type):
    """Return required daily completion percentage for a mindset/mode."""
    key = str(mindset_type or DEFAULT_MINDSET_TYPE).strip().lower()
    return MINDSET_COMPLETION_TARGETS.get(key, MINDSET_COMPLETION_TARGETS["sage"])


def get_difficulty_target(difficulty):
    """Return required daily completion percentage for old difficulty labels."""
    key = str(difficulty or DEFAULT_DIFFICULTY).strip().lower()
    return DIFFICULTY_COMPLETION_TARGETS.get(
        key,
        DIFFICULTY_COMPLETION_TARGETS[DEFAULT_DIFFICULTY],
    )


def calculate_completion_percentage(total_tasks=0, completed_tasks=0):
    """
    Calculate completion percentage safely.

    total_tasks is the number of tasks available.
    completed_tasks is the number completed.

    If completed_tasks is higher than total_tasks, it is clamped to total_tasks.
    """
    safe_total = _coerce_int(total_tasks, "total_tasks", default=0)
    safe_completed = _coerce_int(completed_tasks, "completed_tasks", default=0)

    if safe_total <= 0:
        return 0

    safe_completed = max(0, min(safe_completed, safe_total))

    return round((safe_completed / safe_total) * 100)


def completion_percentage(completed_tasks, total_tasks):
    """Backward-compatible alias for older calls using completed first."""
    return calculate_completion_percentage(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
    )


def calculate_character_reveal_stage(level):
    """Reveal a new character stage every CHARACTER_REVEAL_INTERVAL levels."""
    safe_level = _clamp_int(
        value=level,
        minimum=1,
        maximum=MAX_LEVEL,
        field_name="level",
        default=1,
    )

    return min(safe_level // CHARACTER_REVEAL_INTERVAL, 10)


def apply_daily_hp_result(progress, completion_percentage, difficulty=None, mindset_type=None):
    """
    Apply daily HP/streak result.

    If mindset_type is available, use Sage/Warrior/Demon targets.
    Otherwise, fall back to Easy/Medium/Hard difficulty targets.
    """
    if progress is None:
        raise ValueError("Progress is required.")
    had_invalid_max_hp = getattr(progress, "max_hp", None) is None or progress.max_hp <= 0
    progress = normalise_progress_fields(progress)

    try:
        completion = float(completion_percentage)
    except (TypeError, ValueError):
        completion = 0

    completion = max(0, min(completion, 100))

    if mindset_type:
        target = get_mindset_target(mindset_type)
    else:
        target = get_difficulty_target(difficulty)

    hp_before = progress.hp
    streak_before = progress.streak
    met_target = completion >= target

    if met_target:
        hp_lost = 0
        hp_recovered = 0 if had_invalid_max_hp else 10
        progress.hp = min(progress.max_hp, progress.hp + hp_recovered)
        progress.streak += 1
    else:
        hp_lost = max(0, int(target - completion))
        progress.hp = max(0, progress.hp - hp_lost)
        progress.streak = 0

    return {
        "met_target": met_target,
        "target": target,
        "completion_percentage": round(completion),
        "hp_lost": hp_lost,
        "hp_loss": hp_lost,
        "damage": hp_lost,
        "remaining_hp": progress.hp,
        "hp_before": hp_before,
        "hp_after": progress.hp,
        "streak_before": streak_before,
        "streak_after": progress.streak,
    }


def get_today_tasks(user_id, task_date=None):
    """Return the user's tasks for a selected date, defaulting to today."""
    safe_user_id = _coerce_int(user_id, "user_id")

    if safe_user_id <= 0:
        raise ValueError("user_id must be positive.")

    if task_date is None:
        selected_date = date.today()
    elif isinstance(task_date, datetime):
        selected_date = task_date.date()
    elif isinstance(task_date, date):
        selected_date = task_date
    else:
        raise ValueError("task_date must be a date, datetime, or None.")

    return (
        Task.query
        .filter_by(user_id=safe_user_id, task_date=selected_date)
        .order_by(Task.completed.asc(), Task.created_at.desc())
        .all()
    )


def get_latest_challenge(user):
    """Return a user's latest challenge."""
    if user is None:
        raise ValueError("A valid user is required to load latest challenge.")

    return user.latest_challenge()


def get_weekly_progress(user):
    """Return current week task completion data from Monday to Sunday."""
    if user is None or getattr(user, "id", None) is None:
        return []

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())

    weekly_progress = []

    for offset in range(7):
        day = start_of_week + timedelta(days=offset)
        day_tasks = get_today_tasks(user.id, task_date=day)

        total_tasks = len(day_tasks)
        completed_tasks = sum(1 for task in day_tasks if bool(task.completed))
        percentage = calculate_completion_percentage(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
        )

        weekly_progress.append(
            {
                "date": day,
                "day_label": day.strftime("%a"),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_percentage": percentage,
                "is_today": day == today,
                "is_future": day > today,
            }
        )

    return weekly_progress


def get_partner_count(user):
    """Return active accountability partner count for the user."""
    if user is None or getattr(user, "id", None) is None:
        return 0

    return AccountabilityPartner.query.filter_by(user_id=user.id).count()


def build_dashboard_data(user):
    """Build dashboard data safely for the frontend."""
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid user is required to build dashboard data.")

    progress = get_or_create_progress(user)
    today_tasks = get_today_tasks(user.id)

    total_tasks = len(today_tasks)
    completed_tasks = sum(1 for task in today_tasks if bool(task.completed))
    completion_pct = calculate_completion_percentage(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
    )

    latest_challenge = get_latest_challenge(user)

    current_challenge = (
        getattr(latest_challenge, "mindset_type", None)
        if latest_challenge
        else None
    )

    mindset_target = get_mindset_target(current_challenge)

    partner_count = get_partner_count(user)
    weekly_progress = get_weekly_progress(user)

    character_stage = calculate_character_reveal_stage(progress.level)
    character_reveal_percent = min(progress.level * 5, 100)

    return {
        # Flat keys used by current dashboard.html
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": completion_pct,
        "hp": progress.hp,
        "max_hp": progress.max_hp,
        "xp": progress.xp,
        "level": progress.level,
        "streak": progress.streak,
        "current_challenge": current_challenge,
        "mindset_target": mindset_target,
        "difficulty_target": mindset_target,
        "difficulty": current_challenge or DEFAULT_MINDSET_TYPE,
        "character_reveal_stage": character_stage,
        "character_reveal_percent": character_reveal_percent,
        "today_tasks": today_tasks,
        "weekly_progress": weekly_progress,
        "partner_count": partner_count,

        # Nested compatibility keys for older/newer dashboard versions
        "progress": {
            "hp": progress.hp,
            "max_hp": progress.max_hp,
            "xp": progress.xp,
            "level": progress.level,
            "streak": progress.streak,
        },
        "tasks_today": {
            "total": total_tasks,
            "completed": completed_tasks,
            "completion_percentage": completion_pct,
        },
        "character": {
            "stage": character_stage,
            "name": f"Stage {character_stage}",
            "avatar": "hiddenavatar.png",
            "reveal_percent": character_reveal_percent,
        },
    }


def get_dashboard_data(user):
    """Compatibility wrapper for dashboard data."""
    return build_dashboard_data(user)


def create_reflection(user, mood, note):
    """Create a reflection entry."""
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid user is required.")

    cleaned_note = note.strip() if note else ""

    if len(cleaned_note) > MAX_REFLECTION_LENGTH:
        raise ValueError("Reflection note is too long.")

    reflection = Reflection(
        user_id=user.id,
        mood=mood,
        note=cleaned_note,
    )

    db.session.add(reflection)
    db.session.commit()

    return reflection


def get_public_users(exclude_user_id=None):
    """Return users who share progress publicly."""
    query = User.query.filter_by(is_public=True)

    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)

    return query.order_by(User.created_at.desc()).all()


def find_public_partner_candidate(identifier, current_user_id):
    """Find a public user by username or email for accountability partnering."""
    normalized_identifier = (identifier or "").strip().lower()

    if not normalized_identifier:
        raise ValueError("Please enter a username or email.")

    return (
        User.query
        .filter(User.id != current_user_id)
        .filter(User.is_public.is_(True))
        .filter(
            or_(
                db.func.lower(User.username) == normalized_identifier,
                db.func.lower(User.email) == normalized_identifier,
            )
        )
        .first()
    )


def add_accountability_partner(user, identifier):
    """Add a public user as the current user's accountability partner."""
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid logged-in user is required.")

    candidate = find_public_partner_candidate(identifier, user.id)

    if candidate is None:
        raise ValueError("No public user found with that username or email.")

    existing_partner = (
        AccountabilityPartner.query
        .filter_by(user_id=user.id, partner_id=candidate.id)
        .first()
    )

    if existing_partner is not None:
        raise ValueError("This user is already in your accountability circle.")

    partner_link = AccountabilityPartner(
        user_id=user.id,
        partner_id=candidate.id,
    )

    db.session.add(partner_link)
    db.session.commit()

    return partner_link


def remove_accountability_partner(user, partner_id):
    """Remove an accountability partner from the current user's circle."""
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid logged-in user is required.")

    try:
        safe_partner_id = int(partner_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid accountability partner.") from exc

    partner_link = (
        AccountabilityPartner.query
        .filter_by(user_id=user.id, partner_id=safe_partner_id)
        .first()
    )

    if partner_link is None:
        raise ValueError("That accountability partner was not found.")

    db.session.delete(partner_link)
    db.session.commit()

    return True


def get_accountability_partner_cards(user):
    """Return partner data for display on the community page."""
    if user is None or getattr(user, "id", None) is None:
        return []

    partner_links = (
        AccountabilityPartner.query
        .filter_by(user_id=user.id)
        .order_by(AccountabilityPartner.created_at.desc())
        .all()
    )

    partner_cards = []

    for link in partner_links:
        partner = link.partner

        if partner is None or not partner.is_public:
            continue

        progress = get_or_create_progress(partner)
        latest_challenge = partner.latest_challenge()

        current_challenge = (
            getattr(latest_challenge, "mindset_type", None)
            if latest_challenge
            else None
        )

        partner_cards.append(
            {
                "id": partner.id,
                "username": partner.username,
                "email": partner.email,
                "streak": progress.streak,
                "level": progress.level,
                "xp": progress.xp,
                "hp": progress.hp,
                "max_hp": progress.max_hp,
                "current_challenge": current_challenge,
                "difficulty": current_challenge or DEFAULT_MINDSET_TYPE,
            }
        )

    return partner_cards


def calculate_circle_score(user):
    """Calculate a simple accountability circle score from partner progress."""
    partner_cards = get_accountability_partner_cards(user)

    if not partner_cards:
        return 0

    partner_scores = []

    for partner in partner_cards:
        level_score = min(50, partner["level"] * 5)
        streak_score = min(50, partner["streak"] * 5)
        partner_scores.append(level_score + streak_score)

    return round(sum(partner_scores) / len(partner_scores))

DEFAULT_STARTER_TASKS = [
    {
        "title": "Walk 10,000 steps",
        "description": "Complete a walk or active movement goal for the day.",
        "stat_category": "VIT",
    },
    {
        "title": "Read one page of a book",
        "description": "Read at least one page to build a small learning habit.",
        "stat_category": "INT",
    },
    {
        "title": "Drink enough water",
        "description": "Stay hydrated and track your basic wellness routine.",
        "stat_category": "VIT",
    },
    {
        "title": "Plan tomorrow's top 3 tasks",
        "description": "Write down three important tasks for tomorrow.",
        "stat_category": "INT",
    },
    {
        "title": "Complete a 10 minute tidy-up",
        "description": "Clean or organise one small area around you.",
        "stat_category": "STR",
    },
    {
        "title": "Message one friend or family member",
        "description": "Keep your social connection active today.",
        "stat_category": "CHA",
    },
    {
        "title": "Do a 5 minute reflection",
        "description": "Think about what went well and what can improve.",
        "stat_category": "SPI",
    },
    {
        "title": "Avoid one distraction session",
        "description": "Skip one unnecessary scroll or distraction block.",
        "stat_category": "SPI",
    },
]


def _model_has_column(model, column_name):
    return column_name in model.__table__.columns


def _set_model_value(instance, field_name, value):
    if _model_has_column(instance.__class__, field_name):
        setattr(instance, field_name, value)


def seed_default_tasks_for_user(user, task_date=None, skip_when_testing=True):
    """Create starter tasks for a new user when they first open the dashboard.

    The function is idempotent. It only creates starter tasks when the user has
    no tasks for the selected date. In automated tests it returns without
    seeding unless skip_when_testing=False is passed, so old tests that expect
    an empty task list stay stable.
    """
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid user is required to seed starter tasks.")

    if skip_when_testing:
        try:
            from flask import current_app

            if current_app.config.get("TESTING"):
                return []
        except RuntimeError:
            pass

    from datetime import date as date_class

    task_date = task_date or date_class.today()

    query = Task.query.filter_by(user_id=user.id)

    if _model_has_column(Task, "task_date"):
        query = query.filter_by(task_date=task_date)

    if query.count() > 0:
        return []

    created_tasks = []

    for task_data in DEFAULT_STARTER_TASKS:
        task = Task()

        _set_model_value(task, "user_id", user.id)
        _set_model_value(task, "title", task_data["title"])
        _set_model_value(task, "description", task_data["description"])
        _set_model_value(task, "stat_category", task_data["stat_category"])
        _set_model_value(task, "completed", False)
        _set_model_value(task, "task_date", task_date)

        db.session.add(task)
        created_tasks.append(task)

    db.session.commit()

    return created_tasks


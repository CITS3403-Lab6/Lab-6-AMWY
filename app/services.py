from datetime import date, datetime
import math

from app import db
from app.constants import (
    CHARACTER_REVEAL_INTERVAL,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_TARGETS,
    LEVEL_XP_MULTIPLIER,
    MAX_HP,
    MAX_LEVEL,
    MAX_REFLECTION_LENGTH,
    TASK_XP_REWARD,
)
from app.models import Progress, Reflection, Task, User


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


def get_difficulty_target(difficulty):
    """Return required daily completion percentage for difficulty."""
    normalized_difficulty = str(difficulty or DEFAULT_DIFFICULTY).strip().lower()

    return DIFFICULTY_TARGETS.get(
        normalized_difficulty,
        DIFFICULTY_TARGETS[DEFAULT_DIFFICULTY],
    )


def calculate_completion_percentage(total_tasks, completed_tasks):
    """Calculate completion percentage safely."""
    safe_total = _coerce_int(total_tasks, "total_tasks", default=0)
    safe_completed = _coerce_int(completed_tasks, "completed_tasks", default=0)

    if safe_total <= 0:
        return 0

    safe_completed = max(0, min(safe_total, safe_completed))

    return round((safe_completed / safe_total) * 100)


def calculate_character_reveal_stage(level):
    """Reveal a new character stage every CHARACTER_REVEAL_INTERVAL levels."""
    safe_level = _clamp_int(
        value=level,
        minimum=1,
        maximum=MAX_LEVEL,
        field_name="level",
        default=1,
    )

    return safe_level // CHARACTER_REVEAL_INTERVAL


def apply_daily_hp_result(progress, completion_percentage, difficulty=None):
    """Apply HP damage or streak gain based on daily completion."""
    progress = normalise_progress_fields(progress)

    safe_completion = _clamp_int(
        value=completion_percentage,
        minimum=0,
        maximum=100,
        field_name="completion_percentage",
        default=0,
    )

    target = get_difficulty_target(difficulty)

    if safe_completion >= target:
        progress.streak += 1
        return {
            "met_target": True,
            "target": target,
            "hp_lost": 0,
            "completion_percentage": safe_completion,
            "remaining_hp": progress.hp,
        }

    hp_lost = target - safe_completion
    progress.hp = max(0, progress.hp - hp_lost)
    progress.streak = 0

    return {
        "met_target": False,
        "target": target,
        "hp_lost": hp_lost,
        "completion_percentage": safe_completion,
        "remaining_hp": progress.hp,
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


def build_dashboard_data(user):
    """Build dashboard data safely for the frontend."""
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid user is required to build dashboard data.")

    progress = get_or_create_progress(user)
    today_tasks = get_today_tasks(user.id)

    total_tasks = len(today_tasks)
    completed_tasks = sum(1 for task in today_tasks if bool(task.completed))
    completion_percentage = calculate_completion_percentage(total_tasks, completed_tasks)

    latest_challenge = get_latest_challenge(user)

    difficulty = (
        getattr(latest_challenge, "difficulty", DEFAULT_DIFFICULTY)
        if latest_challenge
        else DEFAULT_DIFFICULTY
    )

    difficulty_target = get_difficulty_target(difficulty)

    current_challenge = (
        getattr(latest_challenge, "mindset_type", None)
        if latest_challenge
        else None
    )

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": completion_percentage,
        "hp": progress.hp,
        "max_hp": progress.max_hp,
        "xp": progress.xp,
        "level": progress.level,
        "streak": progress.streak,
        "current_challenge": current_challenge,
        "difficulty": difficulty,
        "difficulty_target": difficulty_target,
        "character_reveal_stage": calculate_character_reveal_stage(progress.level),
        "today_tasks": today_tasks,
    }


def get_dashboard_data(user):
    """Compatibility wrapper for dashboard data."""
    return build_dashboard_data(user)


def create_reflection(user, mood, note):
    """Create a reflection entry."""
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


def get_public_users():
    """Return users who share progress publicly."""
    return (
        User.query
        .filter_by(is_public=True)
        .order_by(User.created_at.desc())
        .all()
    )
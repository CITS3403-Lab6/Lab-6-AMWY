from app import db
from app.constants import (
    LEVEL_XP_MULTIPLIER,
    MAX_REFLECTION_LENGTH,
    TASK_XP_REWARD,
    VALID_STAT_CATEGORIES,
)
from app.models import Progress, Reflection, User


STAT_XP_FIELD_MAP = {
    "STR": "strength_xp",
    "INT": "intelligence_xp",
    "SPI": "spirituality_xp",
    "VIT": "vitality_xp",
    "CHA": "charisma_xp",
}


def calculate_level_from_xp(xp):
    """
    Convert total XP into a level.

    Level 1: 0-99 XP
    Level 2: 100-199 XP
    Level 3: 200-299 XP
    """
    if xp < 0:
        raise ValueError("XP cannot be negative.")

    return (xp // LEVEL_XP_MULTIPLIER) + 1


def get_or_create_progress(user):
    """
    Ensure a user has a progress record.

    This protects the dashboard and task completion flow if progress data
    is accidentally missing.
    """
    if user.progress is not None:
        return user.progress

    progress = Progress(user_id=user.id)
    db.session.add(progress)
    db.session.commit()

    return progress


def validate_task_category(stat_category):
    """Validate that a task category is supported."""
    if stat_category not in VALID_STAT_CATEGORIES:
        raise ValueError("Invalid stat category.")


def award_task_xp(user, task):
    """
    Award XP to a user for a completed task.

    Returns:
        bool: True if the user levelled up.
    """
    progress = get_or_create_progress(user)

    validate_task_category(task.stat_category)

    old_level = progress.level

    progress.xp += TASK_XP_REWARD

    stat_field = STAT_XP_FIELD_MAP[task.stat_category]
    current_stat_xp = getattr(progress, stat_field)
    setattr(progress, stat_field, current_stat_xp + TASK_XP_REWARD)

    progress.level = calculate_level_from_xp(progress.xp)

    return progress.level > old_level


def complete_user_task(user, task):
    """
    Complete a user's task and award XP exactly once.

    Returns:
        tuple:
            completed_now: True if task changed from incomplete to complete.
            levelled_up: True if completing the task increased the user's level.
    """
    if task.user_id != user.id:
        raise PermissionError("Cannot complete another user's task.")

    if task.completed:
        return False, False

    task.completed = True
    levelled_up = award_task_xp(user, task)
    db.session.commit()

    return True, levelled_up


def create_reflection(user, mood, note):
    """
    Create a reflection entry for a user.

    Blank notes are allowed because a user may only want to record mood.
    Extremely long notes are rejected.
    """
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
    """
    Return only users who have opted into public progress sharing.
    """
    return (
        User.query
        .filter_by(is_public=True)
        .order_by(User.created_at.desc())
        .all()
    )

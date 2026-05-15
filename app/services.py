from datetime import date, datetime
import math

from sqlalchemy import or_

from app import db
from app.constants import (
    CHARACTER_REVEAL_INTERVAL,
    LEVEL_XP_MULTIPLIER,
    MAX_HP,
    MAX_LEVEL,
    TASK_XP_REWARD,
)
from app.models import AccountabilityPartner, Progress, Task, User


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

    # Global XP and level
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
    """Return required daily completion percentage for a mindset type."""
    from app.constants import VALID_MINDSET_TYPES
    
    normalized_mindset = str(mindset_type or "Sage").strip()
    
    mindset_config = VALID_MINDSET_TYPES.get(normalized_mindset)
    if mindset_config:
        return mindset_config.get("min_completion_percentage", 50)
    
    return VALID_MINDSET_TYPES["Sage"]["min_completion_percentage"]


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


def apply_daily_hp_result(progress, completion_percentage, mindset_type=None):
    """Apply HP damage or streak gain based on daily completion."""
    progress = normalise_progress_fields(progress)

    safe_completion = _clamp_int(
        value=completion_percentage,
        minimum=0,
        maximum=100,
        field_name="completion_percentage",
        default=0,
    )

    target = get_mindset_target(mindset_type)

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

    current_challenge = (
        getattr(latest_challenge, "mindset_type", None)
        if latest_challenge
        else None
    )

    mindset_target = get_mindset_target(current_challenge)

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
        "mindset_target": mindset_target,
        "character_reveal_stage": calculate_character_reveal_stage(progress.level),
        "today_tasks": today_tasks,
    }


def get_dashboard_data(user):
    """Compatibility wrapper for dashboard data."""
    return build_dashboard_data(user)


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

    partner_id = int(partner_id)

    partner_link = (
        AccountabilityPartner.query
        .filter_by(user_id=user.id, partner_id=partner_id)
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
                "current_challenge": (
                    getattr(latest_challenge, "mindset_type", None)
                    if latest_challenge
                    else None
                ),
                
                "difficulty": DEFAULT_DIFFICULTY,
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
from datetime import date, datetime
import math

from sqlalchemy import or_

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
from app.models import AccountabilityPartner, Progress, Reflection, Task, User


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
                "difficulty": (
                    getattr(latest_challenge, "difficulty", DEFAULT_DIFFICULTY)
                    if latest_challenge
                    else DEFAULT_DIFFICULTY
                ),
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

# ---------------------------------------------------------------------------
# Compatibility-safe task progression layer
# ---------------------------------------------------------------------------
# Later UI/backend merges simplified task XP into a single XP value. The final
# backend contract still needs both total XP and category XP fields because
# tests, models and existing task data depend on them. These definitions are
# intentionally placed at the end of the module so they override any earlier
# simplified versions while keeping the rest of the file intact.

STAT_XP_FIELD_MAP = {
    "STR": "strength_xp",
    "INT": "intelligence_xp",
    "SPI": "spirituality_xp",
    "VIT": "vitality_xp",
    "CHA": "charisma_xp",
}


def validate_task_category(stat_category):
    """Validate that a task category is supported by the backend contract."""
    if stat_category not in STAT_XP_FIELD_MAP:
        raise ValueError("Invalid stat category.")


def _calculate_level_from_total_xp(xp):
    """Return a stable linear level from total XP, capped at MAX_LEVEL."""
    level_multiplier = globals().get("LEVEL_XP_MULTIPLIER", 100)
    max_level = globals().get("MAX_LEVEL", 100)

    try:
        xp = int(xp or 0)
    except (TypeError, ValueError):
        xp = 0

    if level_multiplier <= 0:
        level_multiplier = 100

    return min(max_level, max(1, (xp // level_multiplier) + 1))


def award_task_xp(user, task):
    """Award total XP and stat-specific XP for a completed task."""
    if user is None or task is None:
        raise ValueError("A valid user and task are required.")

    validate_task_category(task.stat_category)

    progress = get_or_create_progress(user)
    reward = globals().get("TASK_XP_REWARD", 10)

    old_level = progress.level or 1

    progress.xp = int(progress.xp or 0) + reward

    stat_field = STAT_XP_FIELD_MAP[task.stat_category]
    current_stat_xp = getattr(progress, stat_field, 0) or 0
    setattr(progress, stat_field, current_stat_xp + reward)

    progress.level = _calculate_level_from_total_xp(progress.xp)

    return progress.level > old_level


def complete_user_task(user, task):
    """Complete a task once and apply XP safely.

    Returns:
        tuple(bool, bool): completed_now, levelled_up
    """
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid user is required.")

    if task is None or getattr(task, "id", None) is None:
        raise ValueError("A valid task is required.")

    if task.user_id != user.id:
        raise ValueError("You cannot complete another user's task.")

    get_or_create_progress(user)

    if task.completed:
        return False, False

    validate_task_category(task.stat_category)

    task.completed = True
    levelled_up = award_task_xp(user, task)

    db.session.commit()

    return True, levelled_up

# Compatibility-safe accountability circle rendering layer
# This keeps the community/partner backend flexible for different frontend
# naming conventions: current_challenge, challenge_type, goal, difficulty, mode.

def _safe_progress_number(progress, field_name, default=0):
    try:
        return getattr(progress, field_name, default) or default
    except Exception:
        return default


def _latest_challenge_for_partner(partner):
    try:
        from app.models import Challenge

        return (
            Challenge.query
            .filter_by(user_id=partner.id)
            .order_by(Challenge.created_at.desc(), Challenge.id.desc())
            .first()
        )
    except Exception:
        return None


def _extract_challenge_display_data(challenge):
    if challenge is None:
        return {
            "challenge_type": "",
            "current_challenge": "",
            "goal": "",
            "difficulty": "",
            "mindset_type": "",
            "mode": "",
        }

    challenge_type = (
        getattr(challenge, "challenge_type", None)
        or getattr(challenge, "goal", None)
        or ""
    )

    difficulty = getattr(challenge, "difficulty", None) or ""

    mindset_type = (
        getattr(challenge, "mindset_type", None)
        or getattr(challenge, "mode", None)
        or ""
    )

    return {
        "challenge_type": challenge_type,
        "current_challenge": challenge_type,
        "goal": challenge_type,
        "difficulty": difficulty,
        "mindset_type": mindset_type,
        "mode": mindset_type,
    }


def get_accountability_partner_cards(user):
    """Return flexible partner cards for community frontend rendering."""
    if user is None or getattr(user, "id", None) is None:
        return []

    try:
        from app.models import AccountabilityPartner
    except Exception:
        return []

    try:
        partner_links = (
            AccountabilityPartner.query
            .filter_by(user_id=user.id)
            .order_by(AccountabilityPartner.created_at.desc(), AccountabilityPartner.id.desc())
            .all()
        )
    except Exception:
        return []

    partner_cards = []

    for link in partner_links:
        partner = getattr(link, "partner", None)

        if partner is None:
            continue

        if not getattr(partner, "is_public", False):
            continue

        progress = get_or_create_progress(partner)
        challenge = _latest_challenge_for_partner(partner)
        challenge_data = _extract_challenge_display_data(challenge)

        card = {
            "id": partner.id,
            "username": partner.username,
            "email": partner.email,
            "level": _safe_progress_number(progress, "level", 1),
            "xp": _safe_progress_number(progress, "xp", 0),
            "streak": _safe_progress_number(progress, "streak", 0),
            "hp": _safe_progress_number(progress, "hp", 100),
            "max_hp": _safe_progress_number(progress, "max_hp", 100),
        }

        card.update(challenge_data)
        partner_cards.append(card)

    return partner_cards


def calculate_circle_score(user):
    """Calculate a simple score from partner level and streak values."""
    partner_cards = get_accountability_partner_cards(user)

    if not partner_cards:
        return 0

    scores = []

    for partner in partner_cards:
        level = int(partner.get("level", 1) or 1)
        streak = int(partner.get("streak", 0) or 0)

        level_score = min(50, level * 5)
        streak_score = min(50, streak * 5)

        scores.append(level_score + streak_score)

    return round(sum(scores) / len(scores))

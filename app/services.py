from datetime import date, datetime
import math

from app import db
from datetime import date
from app.constants import (
from app.constants import (
    CHARACTER_REVEAL_INTERVAL,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_TARGETS,
    LEVEL_XP_MULTIPLIER,
    MAX_HP,
    MAX_LEVEL,
    MAX_REFLECTION_LENGTH,
    TASK_XP_REWARD,
    VALID_MINDSET_TYPES,
    PLACEHOLDER_CURRENT_HP,
    PLACEHOLDER_MAX_HP,
)
    LEVEL_XP_MULTIPLIER,
    MAX_HP,
    MAX_LEVEL,
    MAX_REFLECTION_LENGTH,
    TASK_XP_REWARD,
    VALID_MINDSET_TYPES,
    PLACEHOLDER_CURRENT_HP,
    PLACEHOLDER_MAX_HP
)
from app.models import Challenge, Progress, Reflection, Task, User


STAT_XP_FIELD_MAP = {
    "STR": "strength_xp",
    "INT": "intelligence_xp",
    "SPI": "spirituality_xp",
    "VIT": "vitality_xp",
    "CHA": "charisma_xp",
}

def get_character_stage(level):
    """
    Determine what character stage a user has reached.

    Args:
        level: The user's current level (like 1, 10, 20, 30, etc)
        
    Returns:
        dict: A dictionary with stage, name, description.
    """

    current_stage = CHARACTER_REVEAL_LEVELS[1]
    for level_threshold in sorted(CHARACTER_REVEAL_LEVELS.keys()):
        if level >= level_threshold:
            current_stage = CHARACTER_REVEAL_LEVELS[level_threshold]
        else:
            break
    
    return current_stage



def _coerce_int(value, field_name, default=None):
    """
    Safely convert a value to int.

    If default is provided, None becomes default.
    Invalid non-numeric values still raise ValueError so bugs are not hidden.
    """
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
    """Convert a value to int and clamp it inside a safe range."""
    number = _coerce_int(value, field_name, default=default)
    return max(minimum, min(maximum, number))


def normalise_progress_fields(progress):
    """
    Repair unsafe progress values before using them in calculations.

    This protects the dashboard from corrupted, missing, or out-of-range
    progress data.
    """
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
    """
    Convert total XP into a capped level.

    Level 1: 0-99 XP
    Level 2: 100-199 XP
    Level cap: 100
    """
    safe_xp = _coerce_int(xp, "XP", default=0)

    if safe_xp < 0:
        raise ValueError("XP cannot be negative.")

    return min((safe_xp // LEVEL_XP_MULTIPLIER) + 1, MAX_LEVEL)


def get_or_create_progress(user):
    """
    Ensure a user has a progress record.

    Also normalises unsafe progress values so old/corrupted records do not
    crash the dashboard or progression calculations.
    """
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
    """
    Award XP to a user for a completed task.

    Returns:
        bool: True if the user levelled up.
    """
    progress = get_or_create_progress(user)

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




def get_difficulty_target(difficulty):
    """
    Return the daily completion percentage needed to avoid HP damage.

    Easy = 50%
    Medium = 70%
    Hard = 90%

    Unknown, blank, or badly-cased difficulty values fall back to medium.
    """
    normalized_difficulty = str(difficulty or DEFAULT_DIFFICULTY).strip().lower()
    return DIFFICULTY_TARGETS.get(
        normalized_difficulty,
        DIFFICULTY_TARGETS[DEFAULT_DIFFICULTY],
    )


def calculate_completion_percentage(total_tasks, completed_tasks):
    """
    Calculate daily task completion percentage safely.

    Handles:
    - zero tasks
    - negative task values
    - completed count greater than total
    - numeric strings
    """
    safe_total = _coerce_int(total_tasks, "total_tasks", default=0)
    safe_completed = _coerce_int(completed_tasks, "completed_tasks", default=0)

    if safe_total <= 0:
        return 0

    safe_completed = max(0, min(safe_total, safe_completed))

    return round((safe_completed / safe_total) * 100)


def calculate_character_reveal_stage(level):
    """
    Reveal a new character stage every 10 levels.

    Level 1-9 = stage 0
    Level 10 = stage 1
    Level 20 = stage 2
    Level 100 = stage 10
    """
    safe_level = _clamp_int(
        value=level,
        minimum=1,
        maximum=MAX_LEVEL,
        field_name="level",
        default=1,
    )

    return safe_level // CHARACTER_REVEAL_INTERVAL


def apply_daily_hp_result(progress, completion_percentage, difficulty=None):
    """
    Apply HP damage or streak gain based on daily completion percentage.

    This function does not commit by itself. The caller should commit after
    applying the result.

    Defensive behaviour:
    - clamps completion percentage between 0 and 100
    - falls back invalid difficulty to medium
    - repairs unsafe HP/max HP/streak values
    - never allows HP to drop below zero
    """
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
    """Return the user's tasks for a specific date, defaulting to today."""
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
    """Return a user's latest challenge, if one exists."""
    if user is None:
        raise ValueError("A valid user is required to load latest challenge.")

    return user.latest_challenge()


def build_dashboard_data(user):
    """
    Build clean dashboard data for frontend use.

    This keeps the dashboard template from needing to understand backend
    progression calculations and provides safe fallback values.
    """
    if user is None or getattr(user, "id", None) is None:
        raise ValueError("A valid user is required to build dashboard data.")

    progress = get_or_create_progress(user)
    today_tasks = get_today_tasks(user.id)

    total_tasks = len(today_tasks)
    completed_tasks = sum(1 for task in today_tasks if bool(task.completed))
    completion_percentage = calculate_completion_percentage(total_tasks, completed_tasks)

    latest_challenge = get_latest_challenge(user)
    difficulty = latest_challenge.difficulty if latest_challenge else DEFAULT_DIFFICULTY
    difficulty_target = get_difficulty_target(difficulty)

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": completion_percentage,
        "hp": progress.hp,
        "max_hp": progress.max_hp,
        "xp": progress.xp,
        "level": progress.level,
        "streak": progress.streak,
        "current_challenge": latest_challenge.challenge_type if latest_challenge else None,
        "difficulty": difficulty,
        "difficulty_target": difficulty_target,
        "character_reveal_stage": calculate_character_reveal_stage(progress.level),
        "today_tasks": today_tasks,
    }

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

def get_today_tasks(user):
    "Return list of tasks created today for the user."
    today = date.today()
    return (
        Task.query
        .filter_by(user_id=user.id, task_date=today)
        .order_by(Task.completed.asc(), Task.created_at.desc())
        .all()
    )

def get_dashboard_data(user):
    """
    Returns dictionary of dashboard data in one package
        - HP (placeholder for now)
        - Level
        - XP progress
        - Streak
        - Today's tasks
        - Daily completion percentage
        - Current challenge/difficulty
        - Character stage
    """

    progress = get_or_create_progress(user)
    today_tasks = get_today_tasks(user)
    total_today = len(today_tasks)
    completed_today = sum(1 for task in today_tasks if task.completed)

    if total_today > 0:
        completion_percentage = (completed_today / total_today) * 100
    else:
        completion_percentage = 0

    xp_for_current_level = (progress.level - 1) * LEVEL_XP_MULTIPLIER
    xp_for_next_level = progress.level * LEVEL_XP_MULTIPLIER
    xp_progress = progress.xp - xp_for_current_level
    xp_for_next_level_gap = xp_for_next_level - xp_for_current_level
    
    if xp_for_next_level_gap > 0:
        xp_progress_percentage = (xp_progress / xp_for_next_level_gap) * 100
    else:
        xp_progress_percentage = 0
    
    latest_challenge = user.latest_challenge()
    mindset_data = {}
    mindset_requirement = 0
    
    if latest_challenge:
        mindset_type = latest_challenge.mindset_type
        mindset_info = VALID_MINDSET_TYPES.get(mindset_type, {})
        mindset_requirement = mindset_info.get("min_completion_percentage", 0)

        mindset_data = {
            "mindset": mindset_type,
            "name": mindset_info.get("name", mindset_type),
            "description": mindset_info.get("description", ""),
            "min_completion_percentage": mindset_requirement,
        }

    character_stage = get_character_stage(progress.level)

    dashboard_data = {
  
        "hp": {
            "current": PLACEHOLDER_CURRENT_HP,
            "max": PLACEHOLDER_MAX_HP,
        },
        

        "progress": {
            "level": progress.level,
            "xp": progress.xp,
            "xp_progress_percentage": round(xp_progress_percentage, 1),
        },
        

        "streak": progress.streak,
        

        "tasks_today": {
            "total": total_today,
            "completed": completed_today,
            "completion_percentage": round(completion_percentage, 1),
        },
        
        "mindset": mindset_data,
        "mindset_requirement": mindset_requirement,
        
        # Character info
        "character": {
            "stage": character_stage["stage"],
            "name": character_stage["name"],
            "description": character_stage["description"],
        },
    }
    
    return dashboard_data
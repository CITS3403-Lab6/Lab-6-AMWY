from app import db
from datetime import date
from app.constants import (
    CHARACTER_REVEAL_LEVELS, 
    LEVEL_XP_MULTIPLIER,
    MAX_REFLECTION_LENGTH,
    TASK_XP_REWARD,
    VALID_MINDSET_TYPES,
    PLACEHOLDER_CURRENT_HP,
    PLACEHOLDER_MAX_HP
)
from app.models import Progress, Reflection, User, Task, Challenge


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


#To be removed
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
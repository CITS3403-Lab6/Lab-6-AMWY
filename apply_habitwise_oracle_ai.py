from pathlib import Path
import re
import shutil

FILES = [
    Path("app/services.py"),
    Path("app/routes.py"),
    Path("app/templates/dashboard.html"),
    Path("static/css/dashboard.css"),
]

for file_path in FILES[:3]:
    if not file_path.exists():
        raise SystemExit(f"Missing required file: {file_path}")

for file_path in FILES:
    if file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(file_path, backup_path)

services_path = Path("app/services.py")
routes_path = Path("app/routes.py")
dashboard_path = Path("app/templates/dashboard.html")
css_path = Path("static/css/dashboard.css")
tests_path = Path("tests/test_habitwise_oracle.py")

services = services_path.read_text()

oracle_service_block = r'''

# ---------------------------------------------------------------------------
# HabitWise Oracle AI
# ---------------------------------------------------------------------------
# A deterministic, backend-driven AI-style coach.
# It reads existing user/task/challenge/progress data and returns a structured
# insight dictionary. It does not call external APIs and does not write to DB.

ORACLE_ARCHETYPES = {
    "sage": {
        "name": "Sage",
        "tone_class": "sage",
        "fallback_target": 50,
        "voice": "calm, reflective and strategic",
    },
    "warrior": {
        "name": "Warrior",
        "tone_class": "warrior",
        "fallback_target": 70,
        "voice": "direct, disciplined and action-focused",
    },
    "demon": {
        "name": "Demon",
        "tone_class": "demon",
        "fallback_target": 90,
        "voice": "intense, ambitious and high-pressure",
    },
}

ORACLE_DIFFICULTY_TARGETS = {
    "easy": 50,
    "medium": 70,
    "hard": 90,
}

ORACLE_LORE_LINES = {
    "Sage": {
        "complete": "The Sage closes the scroll. Today’s lesson has been honoured.",
        "on_track": "The Sage sees a steady current: your rhythm is forming before the day ends.",
        "at_risk": "The Sage senses drifting focus. The path is still open, but it needs intention.",
        "critical": "The Sage warns that the flame is dim. One deliberate action can still protect the day.",
    },
    "Warrior": {
        "complete": "The Warrior marks the field as cleared. Discipline has answered the call.",
        "on_track": "The Warrior is advancing. Momentum is present, but the mission is not finished.",
        "at_risk": "The Warrior is losing ground. Regain control with one immediate strike.",
        "critical": "The Warrior is under siege. Drop the noise and move before the day is lost.",
    },
    "Demon": {
        "complete": "The Demon smiles at the ruins of completed quests. The standard was met.",
        "on_track": "The Demon is still hunting. You have momentum, but hunger must become action.",
        "at_risk": "The Demon rejects weak progress. The gap is visible; close it.",
        "critical": "The Demon is starving. Comfort is winning unless you attack the next task now.",
    },
}


def _oracle_get(obj, *names, default=None):
    if obj is None:
        return default

    for name in names:
        if isinstance(obj, dict) and name in obj:
            value = obj.get(name)
            return default if value is None else value

        value = getattr(obj, name, None)
        if value is not None:
            return value

    return default


def _oracle_as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _oracle_as_bool(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on", "complete", "completed"}

    return bool(value)


def _oracle_percent(completed, total):
    if total <= 0:
        return 0

    return round((completed / total) * 100, 1)


def _oracle_period(hour):
    if hour < 6:
        return "late night"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    if hour < 21:
        return "evening"
    return "night"


def _oracle_detect_archetype(challenge):
    raw = _oracle_get(
        challenge,
        "mindset_type",
        "mode",
        "archetype",
        "character_type",
        "challenge_type",
        "goal",
        default="Sage",
    )

    raw_text = str(raw).strip().lower()

    if "demon" in raw_text or "chaos" in raw_text or "intense" in raw_text:
        return "Demon"

    if "warrior" in raw_text or "action" in raw_text or "discipline" in raw_text:
        return "Warrior"

    return "Sage"


def _oracle_detect_goal(challenge):
    goal = _oracle_get(
        challenge,
        "challenge_type",
        "goal",
        "name",
        "title",
        default="daily growth",
    )

    return str(goal).replace("_", " ").title()


def _oracle_detect_target(challenge, archetype):
    difficulty = _oracle_get(challenge, "difficulty", "tier", "challenge_level", default=None)

    if difficulty:
        target = ORACLE_DIFFICULTY_TARGETS.get(str(difficulty).strip().lower())

        if target is not None:
            return target

    archetype_key = archetype.lower()

    return ORACLE_ARCHETYPES.get(archetype_key, ORACLE_ARCHETYPES["sage"])["fallback_target"]


def _oracle_status(completion_percentage, target, completed, total, hp):
    if total == 0:
        return "empty"

    if completed == total:
        return "complete"

    if completion_percentage >= target:
        return "on_track"

    if hp <= 30 or completion_percentage < max(15, target * 0.35):
        return "critical"

    return "at_risk"


def _oracle_task_title(task):
    title = _oracle_get(task, "title", "name", "description", default="Unnamed task")

    return str(title).strip() or "Unnamed task"


def _oracle_task_completed(task):
    return _oracle_as_bool(
        _oracle_get(task, "completed", "done", "is_complete", "is_done", default=False)
    )


def _oracle_rank_remaining_tasks(tasks):
    remaining = []

    for task in tasks:
        if not _oracle_task_completed(task):
            remaining.append(_oracle_task_title(task))

    return remaining[:3]


def _oracle_build_summary(archetype, goal, completed, total, pct, target, hp, max_hp, streak, level, period):
    if total == 0:
        return (
            f"The {archetype} has no quests to read yet. Add tasks to begin today’s {goal.lower()} run."
        )

    return (
        f"The {archetype} reads your {period}: {completed}/{total} quests complete "
        f"({pct}%). Your target is {target}%, HP is {hp}/{max_hp}, "
        f"streak is {streak}, and level is {level}."
    )


def _oracle_build_recommendation(archetype, status, target, pct, remaining_tasks):
    if status == "empty":
        return "Add 3 clear quests for today so the Oracle can guide your run."

    if status == "complete":
        return "Your daily board is cleared. Do not overload the day; plan tomorrow with intention."

    if status == "on_track":
        if remaining_tasks:
            return f"You are above target. Finish “{remaining_tasks[0]}” next to secure the day cleanly."
        return "You are above target. Keep the pace steady and avoid adding unnecessary noise."

    if status == "critical":
        if archetype == "Demon":
            return "You are far below standard. Pick the hardest remaining quest and attack it now."
        if archetype == "Warrior":
            return "The day is slipping. Start one remaining quest immediately and rebuild momentum."
        return "Focus is fading. Choose one small quest and complete it before thinking about the rest."

    if remaining_tasks:
        return f"You are below the {target}% target. Complete “{remaining_tasks[0]}” to move back toward safety."

    return f"You are below the {target}% target. Complete one task now to protect HP and streak."


def _oracle_build_next_actions(status, archetype, remaining_tasks, pct, target, period):
    if status == "complete":
        return [
            "Log one reflection about what worked today.",
            "Prepare tomorrow’s first quest before closing the app.",
            "Stop adding extra tasks just to chase numbers.",
        ]

    if status == "empty":
        return [
            "Add one health quest.",
            "Add one learning or work quest.",
            "Add one reflection or social quest.",
        ]

    chosen = remaining_tasks[:3]

    while len(chosen) < 3:
        if len(chosen) == 0:
            chosen.append("Complete the smallest remaining quest first.")
        elif len(chosen) == 1:
            chosen.append(f"Push completion from {pct}% closer to the {target}% target.")
        else:
            chosen.append(f"Review progress again before the end of the {period}.")

    if archetype == "Demon" and status in {"critical", "at_risk"}:
        chosen[0] = f"Attack this first: {chosen[0]}"

    if archetype == "Warrior" and status in {"critical", "at_risk"}:
        chosen[0] = f"Start immediately: {chosen[0]}"

    if archetype == "Sage" and status in {"critical", "at_risk"}:
        chosen[0] = f"Choose calmly and finish: {chosen[0]}"

    return chosen[:3]


def _oracle_confidence(total, completed, challenge, progress):
    score = 50

    if total > 0:
        score += 20

    if completed > 0:
        score += 10

    if challenge is not None:
        score += 10

    if progress is not None:
        score += 10

    return min(score, 100)


def build_smart_coach_analysis(user, tasks=None, challenge=None, progress=None):
    """Build a deterministic AI-style daily coach analysis.

    This is intentionally not an external LLM call. It behaves like a mini AI
    coach by combining real app signals into a structured recommendation.
    """
    from datetime import datetime

    task_list = list(tasks or [])

    if progress is None:
        progress = _oracle_get(user, "progress", default=None)

    if challenge is None:
        try:
            latest_challenge = getattr(user, "latest_challenge", None)

            if callable(latest_challenge):
                challenge = latest_challenge()
            else:
                challenge = latest_challenge

        except Exception:
            challenge = None

    now = datetime.now()
    period = _oracle_period(now.hour)

    archetype = _oracle_detect_archetype(challenge)
    goal = _oracle_detect_goal(challenge)
    target = _oracle_detect_target(challenge, archetype)

    completed = sum(1 for task in task_list if _oracle_task_completed(task))
    total = len(task_list)
    pct = _oracle_percent(completed, total)

    hp = _oracle_as_int(_oracle_get(progress, "hp", default=_oracle_get(user, "hp", default=100)), 100)
    max_hp = _oracle_as_int(_oracle_get(progress, "max_hp", default=_oracle_get(user, "max_hp", default=100)), 100)
    xp = _oracle_as_int(_oracle_get(progress, "xp", default=_oracle_get(user, "xp", default=0)), 0)
    level = _oracle_as_int(_oracle_get(progress, "level", default=_oracle_get(user, "level", default=1)), 1)
    streak = _oracle_as_int(_oracle_get(progress, "streak", default=_oracle_get(user, "streak", default=0)), 0)

    hp = max(0, hp)
    max_hp = max(1, max_hp)

    status = _oracle_status(pct, target, completed, total, hp)
    remaining_tasks = _oracle_rank_remaining_tasks(task_list)

    title_map = {
        "Sage": "HabitWise Oracle: Sage Reading",
        "Warrior": "HabitWise Oracle: Warrior Briefing",
        "Demon": "HabitWise Oracle: Demon Audit",
    }

    title = title_map.get(archetype, "HabitWise Oracle")
    lore = ORACLE_LORE_LINES.get(archetype, ORACLE_LORE_LINES["Sage"]).get(status)

    if lore is None:
        lore = ORACLE_LORE_LINES.get(archetype, ORACLE_LORE_LINES["Sage"])["on_track"]

    summary = _oracle_build_summary(
        archetype=archetype,
        goal=goal,
        completed=completed,
        total=total,
        pct=pct,
        target=target,
        hp=hp,
        max_hp=max_hp,
        streak=streak,
        level=level,
        period=period,
    )

    recommendation = _oracle_build_recommendation(
        archetype=archetype,
        status=status,
        target=target,
        pct=pct,
        remaining_tasks=remaining_tasks,
    )

    next_actions = _oracle_build_next_actions(
        status=status,
        archetype=archetype,
        remaining_tasks=remaining_tasks,
        pct=pct,
        target=target,
        period=period,
    )

    confidence = _oracle_confidence(total, completed, challenge, progress)

    return {
        "title": title,
        "archetype": archetype,
        "goal": goal,
        "status": status,
        "summary": summary,
        "lore": lore,
        "recommendation": recommendation,
        "next_actions": next_actions,
        "tone_class": archetype.lower(),
        "completed": completed,
        "total": total,
        "pct": pct,
        "target": target,
        "hp": hp,
        "max_hp": max_hp,
        "xp": xp,
        "level": level,
        "streak": streak,
        "period": period,
        "confidence": confidence,
        "remaining_tasks": remaining_tasks,
    }
'''

if "def build_smart_coach_analysis(" not in services:
    services = services.rstrip() + oracle_service_block + "\n"

services_path.write_text(services)


routes = routes_path.read_text()

if "build_smart_coach_analysis" not in routes:
    if "from app.services import (" in routes:
        routes = routes.replace(
            "from app.services import (\n",
            "from app.services import (\n    build_smart_coach_analysis,\n",
            1,
        )
    else:
        routes = routes.replace(
            "from app.services import ",
            "from app.services import build_smart_coach_analysis, ",
            1,
        )

dashboard_match = re.search(r"\ndef dashboard\([^)]*\):", routes)

if dashboard_match and "HabitWise Oracle dashboard analysis" not in routes:
    dashboard_start = dashboard_match.start()
    next_route = routes.find("\n@main.route", dashboard_match.end())

    if next_route == -1:
        next_route = len(routes)

    dashboard_block = routes[dashboard_start:next_route]

    render_match = re.search(r"\n\s*return render_template\(", dashboard_block)

    if render_match:
        insert_at = dashboard_start + render_match.start()

        smart_call = '''
    # HabitWise Oracle dashboard analysis
    try:
        smart_coach = build_smart_coach_analysis(
            user=current_user,
            tasks=tasks if "tasks" in locals() else [],
            challenge=challenge if "challenge" in locals() else current_user.latest_challenge(),
            progress=progress if "progress" in locals() else getattr(current_user, "progress", None),
        )
    except Exception:
        smart_coach = None

'''

        routes = routes[:insert_at] + smart_call + routes[insert_at:]

        dashboard_match = re.search(r"\ndef dashboard\([^)]*\):", routes)
        dashboard_start = dashboard_match.start()
        next_route = routes.find("\n@main.route", dashboard_match.end())

        if next_route == -1:
            next_route = len(routes)

        dashboard_block = routes[dashboard_start:next_route]

        if "smart_coach=smart_coach" not in dashboard_block:
            dashboard_block = re.sub(
                r'render_template\((["\']dashboard\.html["\']),',
                r'render_template(\1,\n        smart_coach=smart_coach,',
                dashboard_block,
                count=1,
            )

        routes = routes[:dashboard_start] + dashboard_block + routes[next_route:]

routes_path.write_text(routes)


dashboard = dashboard_path.read_text()

oracle_card = '''
<section class="smart-coach-oracle oracle-{{ smart_coach.tone_class if smart_coach else 'neutral' }}">
  {% if smart_coach %}
    <div class="oracle-header">
      <div>
        <p class="oracle-kicker">HabitWise Oracle</p>
        <h2 class="oracle-title">{{ smart_coach.title }}</h2>
      </div>
      <div class="oracle-pill">
        {{ smart_coach.archetype }} · {{ smart_coach.status.replace("_", " ").title() }}
      </div>
    </div>

    <p class="oracle-summary">{{ smart_coach.summary }}</p>

    <div class="oracle-meter">
      <div class="oracle-meter-fill" style="width: {{ [smart_coach.pct, 100]|min }}%;"></div>
    </div>

    <p class="oracle-meta">
      {{ smart_coach.completed }}/{{ smart_coach.total }} quests · Target {{ smart_coach.target }}% · Confidence {{ smart_coach.confidence }}%
    </p>

    <blockquote class="oracle-lore">
      {{ smart_coach.lore }}
    </blockquote>

    <div class="oracle-recommendation">
      <strong>Oracle recommendation:</strong>
      <span>{{ smart_coach.recommendation }}</span>
    </div>

    <ul class="oracle-actions">
      {% for action in smart_coach.next_actions %}
        <li>{{ action }}</li>
      {% endfor %}
    </ul>
  {% endif %}
</section>
'''

if "smart-coach-oracle" not in dashboard:
    if "{% block content %}" in dashboard:
        dashboard = dashboard.replace(
            "{% block content %}",
            "{% block content %}\n" + oracle_card,
            1,
        )
    elif "<main" in dashboard:
        main_index = dashboard.find("<main")
        main_end = dashboard.find(">", main_index)

        dashboard = dashboard[:main_end + 1] + "\n" + oracle_card + "\n" + dashboard[main_end + 1:]
    elif "<body" in dashboard:
        body_index = dashboard.find("<body")
        body_end = dashboard.find(">", body_index)

        dashboard = dashboard[:body_end + 1] + "\n" + oracle_card + "\n" + dashboard[body_end + 1:]
    else:
        dashboard = oracle_card + "\n" + dashboard

dashboard_path.write_text(dashboard)


css_path.parent.mkdir(parents=True, exist_ok=True)

css = css_path.read_text() if css_path.exists() else ""

oracle_css = r'''

.smart-coach-oracle {
  margin: 20px 0;
  padding: 22px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background:
    radial-gradient(circle at top right, rgba(125, 92, 246, 0.22), transparent 32%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.94));
  color: #e5e7eb;
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.24);
  position: relative;
  overflow: hidden;
}

.smart-coach-oracle::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 5px;
  background: var(--oracle-accent, #8b5cf6);
}

.smart-coach-oracle.oracle-sage {
  --oracle-accent: #22d3ee;
}

.smart-coach-oracle.oracle-warrior {
  --oracle-accent: #f59e0b;
}

.smart-coach-oracle.oracle-demon {
  --oracle-accent: #ef4444;
}

.oracle-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.oracle-kicker {
  margin: 0 0 4px;
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--oracle-accent, #8b5cf6);
  font-weight: 800;
}

.oracle-title {
  margin: 0;
  color: #f8fafc;
  font-size: 1.18rem;
}

.oracle-pill {
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #f8fafc;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 0.74rem;
  background: rgba(255, 255, 255, 0.08);
}

.oracle-summary {
  margin: 0 0 14px;
  color: #cbd5e1;
  line-height: 1.6;
}

.oracle-meter {
  width: 100%;
  height: 8px;
  background: rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 8px;
}

.oracle-meter-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--oracle-accent, #8b5cf6);
  transition: width 0.35s ease;
}

.oracle-meta {
  margin: 0 0 14px;
  font-size: 0.82rem;
  color: #94a3b8;
}

.oracle-lore {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-left: 3px solid var(--oracle-accent, #8b5cf6);
  background: rgba(15, 23, 42, 0.72);
  color: #cbd5e1;
  border-radius: 0 12px 12px 0;
  font-style: italic;
  line-height: 1.55;
}

.oracle-recommendation {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  color: #e2e8f0;
  margin-bottom: 12px;
  line-height: 1.5;
}

.oracle-actions {
  margin: 0;
  padding-left: 20px;
  color: #cbd5e1;
}

.oracle-actions li {
  margin: 5px 0;
  line-height: 1.45;
}

@media (max-width: 720px) {
  .oracle-header {
    flex-direction: column;
  }

  .oracle-pill {
    white-space: normal;
  }
}
'''

if ".smart-coach-oracle" not in css:
    css = css.rstrip() + oracle_css + "\n"

css_path.write_text(css)


tests_path.parent.mkdir(parents=True, exist_ok=True)

tests_path.write_text(r'''from app import db
from app.models import Challenge, Progress, Task, User
from app.services import build_smart_coach_analysis


class FakeTask:
    def __init__(self, title, completed):
        self.title = title
        self.completed = completed


class FakeProgress:
    hp = 75
    max_hp = 100
    xp = 300
    level = 4
    streak = 6


class FakeChallenge:
    mindset_type = "Demon"
    difficulty = "hard"
    challenge_type = "study"


def test_oracle_handles_no_tasks():
    result = build_smart_coach_analysis(
        user={},
        tasks=[],
        challenge=None,
        progress=None,
    )

    assert result["total"] == 0
    assert result["status"] == "empty"
    assert result["archetype"] == "Sage"
    assert len(result["next_actions"]) == 3


def test_oracle_detects_demon_and_hard_target():
    tasks = [
        FakeTask("Finish report", True),
        FakeTask("Review notes", False),
        FakeTask("Submit draft", False),
    ]

    result = build_smart_coach_analysis(
        user={},
        tasks=tasks,
        challenge=FakeChallenge(),
        progress=FakeProgress(),
    )

    assert result["archetype"] == "Demon"
    assert result["target"] == 90
    assert result["completed"] == 1
    assert result["total"] == 3
    assert "Review notes" in " ".join(result["next_actions"]) or "Submit draft" in " ".join(result["next_actions"])


def test_oracle_complete_status():
    tasks = [
        FakeTask("Task one", True),
        FakeTask("Task two", True),
    ]

    result = build_smart_coach_analysis(
        user={},
        tasks=tasks,
        challenge={"mode": "Warrior", "difficulty": "easy"},
        progress={"hp": 100, "max_hp": 100, "xp": 500, "level": 5, "streak": 10},
    )

    assert result["status"] == "complete"
    assert result["archetype"] == "Warrior"
    assert result["pct"] == 100.0


def test_oracle_dashboard_renders(client, app):
    response = client.post(
        "/signup",
        data={
            "username": "oracleuser",
            "email": "oracle@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    dashboard_response = client.get("/dashboard")

    assert dashboard_response.status_code == 200
    assert b"HabitWise Oracle" in dashboard_response.data
''')


print("HabitWise Oracle AI patch applied.")

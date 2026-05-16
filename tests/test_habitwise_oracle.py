from app import db
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

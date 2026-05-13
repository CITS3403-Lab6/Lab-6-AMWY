"""
Comprehensive tests for HabitWise features including:
- Authentication (signup, login, logout)
- Model creation and relationships
- Challenge saving and retrieval
- Task completion and XP/level updates
- Community privacy filtering
"""

import pytest
from app import db
from app.models import User, Progress, Task, Challenge, Reflection
from app.services import complete_user_task, calculate_level_from_xp


# ============================================
# AUTHENTICATION TESTS - Signup
# ============================================

def test_signup_with_valid_credentials_creates_user(client, app):
    """Test that signup with valid credentials creates a user and progress record."""
    response = client.post(
        "/signup",
        data={
            "username": "newwarrior",
            "email": "warrior@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Account created" in response.data or b"Dashboard" in response.data

    with app.app_context():
        user = User.query.filter_by(username="newwarrior").first()
        assert user is not None
        assert user.email == "warrior@example.com"
        assert user.check_password("SecurePass123!")
        assert user.progress is not None
        assert user.progress.level == 1


def test_signup_with_mismatched_passwords_fails(client, app):
    """Test that signup with mismatched passwords is rejected."""
    response = client.post(
        "/signup",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Password123!",
            "confirm_password": "DifferentPass123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Passwords must match" in response.data

    with app.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is None


def test_signup_with_existing_username_fails(client, app):
    """Test that signup with an existing username is rejected."""
    # Create first user
    client.post(
        "/signup",
        data={
            "username": "samename",
            "email": "first@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )

    client.get("/logout")

    # Try to create another user with same username
    response = client.post(
        "/signup",
        data={
            "username": "samename",
            "email": "second@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"already taken" in response.data or b"Username" in response.data

    with app.app_context():
        users = User.query.filter_by(username="samename").all()
        assert len(users) == 1


def test_signup_with_existing_email_fails(client, app):
    """Test that signup with an existing email is rejected."""
    # Create first user
    client.post(
        "/signup",
        data={
            "username": "user1",
            "email": "sameemail@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )

    client.get("/logout")

    # Try to create another user with same email
    response = client.post(
        "/signup",
        data={
            "username": "user2",
            "email": "sameemail@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"already registered" in response.data or b"Email" in response.data


def test_signup_redirects_to_dashboard_when_logged_in(client, app):
    """Test that accessing signup when already logged in redirects to dashboard."""
    # Create and login user
    client.post(
        "/signup",
        data={
            "username": "loggeduser",
            "email": "logged@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )

    response = client.get("/signup", follow_redirects=False)
    assert response.status_code == 302  # Redirect


# ============================================
# AUTHENTICATION TESTS - Login & Logout
# ============================================

def test_login_with_valid_credentials(client, sample_user):
    """Test that login with correct credentials works."""
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Logged in successfully" in response.data or b"Dashboard" in response.data


def test_login_with_incorrect_password(client, sample_user):
    """Test that login with wrong password fails."""
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "wrongpassword",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_login_with_nonexistent_user(client):
    """Test that login with non-existent user fails."""
    response = client.post(
        "/login",
        data={
            "username": "nonexistent",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_logout_clears_session(client, sample_user):
    """Test that logout clears the user session."""
    # Login first
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # Verify dashboard accessible
    response = client.get("/dashboard")
    assert response.status_code == 200

    # Logout
    logout_response = client.get("/logout", follow_redirects=True)
    assert b"logged out" in logout_response.data or b"Logged out" in logout_response.data

    # Verify dashboard not accessible
    protected_response = client.get("/dashboard", follow_redirects=True)
    assert b"Login" in protected_response.data or b"log in" in protected_response.data


def test_login_redirects_to_dashboard_when_already_logged_in(client, sample_user):
    """Test that accessing login when already logged in redirects to dashboard."""
    # Login first
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # Try to access login page
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302  # Redirect


# ============================================
# MODEL CREATION TESTS
# ============================================

def test_user_model_creation(app):
    """Test basic user model creation and attributes."""
    user = User(username="modeltest", email="model@example.com")
    user.set_password("testpass123")

    with app.app_context():
        db.session.add(user)
        db.session.commit()

        saved_user = User.query.filter_by(username="modeltest").first()
        assert saved_user is not None
        assert saved_user.email == "model@example.com"
        assert saved_user.is_public is True  # Default value
        assert saved_user.check_password("testpass123")


def test_progress_model_creation(app):
    """Test progress model creation and default values."""
    user = User(username="proguser", email="prog@example.com")
    user.set_password("pass123")
    progress = Progress(user=user)

    with app.app_context():
        db.session.add(user)
        db.session.add(progress)
        db.session.commit()

        saved_progress = Progress.query.filter_by(user_id=user.id).first()
        assert saved_progress is not None
        assert saved_progress.level == 1
        assert saved_progress.xp == 0
        assert saved_progress.streak == 0
        assert saved_progress.strength_xp == 0
        assert saved_progress.intelligence_xp == 0
        assert saved_progress.spirituality_xp == 0
        assert saved_progress.vitality_xp == 0
        assert saved_progress.charisma_xp == 0


def test_task_model_creation(app, sample_user):
    """Test task model creation."""
    task = Task(
        user_id=sample_user.id,
        title="Complete a workout",
        stat_category="STR",
    )

    with app.app_context():
        db.session.add(task)
        db.session.commit()

        saved_task = Task.query.filter_by(title="Complete a workout").first()
        assert saved_task is not None
        assert saved_task.completed is False
        assert saved_task.stat_category == "STR"


def test_challenge_model_creation(app, sample_user):
    """Test challenge model creation."""
    challenge = Challenge(
        user_id=sample_user.id,
        challenge_type="fitness",
        difficulty="hard",
        mindset_type="Warrior",
    )

    with app.app_context():
        db.session.add(challenge)
        db.session.commit()

        saved_challenge = Challenge.query.filter_by(user_id=sample_user.id).first()
        assert saved_challenge is not None
        assert saved_challenge.challenge_type == "fitness"
        assert saved_challenge.difficulty == "hard"
        assert saved_challenge.mindset_type == "Warrior"


def test_reflection_model_creation(app, sample_user):
    """Test reflection model creation."""
    reflection = Reflection(
        user_id=sample_user.id,
        mood="energized",
        note="Great progress on the challenge!",
    )

    with app.app_context():
        db.session.add(reflection)
        db.session.commit()

        saved_reflection = Reflection.query.filter_by(user_id=sample_user.id).first()
        assert saved_reflection is not None
        assert saved_reflection.mood == "energized"
        assert saved_reflection.note == "Great progress on the challenge!"


# ============================================
# CHALLENGE SAVING TESTS
# ============================================

def test_save_challenge_creates_challenge(client, sample_user, app):
    """Test that saving a challenge creates it in the database."""
    # Login
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # Save challenge
    response = client.post(
        "/dashboard",
        data={
            "challenge_type": "study",
            "difficulty": "medium",
            "mindset_type": "Sage",
            "is_public": False,
            "save_challenge": "on",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"saved successfully" in response.data or b"Challenge" in response.data

    with app.app_context():
        challenge = Challenge.query.filter_by(user_id=sample_user.id).first()
        assert challenge is not None
        assert challenge.challenge_type == "study"
        assert challenge.difficulty == "medium"
        assert challenge.mindset_type == "Sage"


def test_save_challenge_updates_is_public_flag(client, sample_user, app):
    """Test that saving a challenge updates the user's is_public flag."""
    # Login
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # Save challenge with is_public checked
    client.post(
        "/dashboard",
        data={
            "challenge_type": "fitness",
            "difficulty": "easy",
            "mindset_type": "Warrior",
            "is_public": "on",
            "save_challenge": "on",
        },
    )

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.is_public is True


def test_save_challenge_without_is_public_flag(client, sample_user, app):
    """Test that saving a challenge without is_public flag sets user to private."""
    # Login
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # First set to public
    sample_user.is_public = True
    with app.app_context():
        db.session.commit()

    # Save challenge without is_public
    client.post(
        "/dashboard",
        data={
            "challenge_type": "fitness",
            "difficulty": "easy",
            "mindset_type": "Warrior",
            "save_challenge": "on",
        },
    )

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.is_public is False


def test_latest_challenge_returned_in_dashboard(client, sample_user, app):
    """Test that the dashboard shows the latest challenge."""
    # Create two challenges
    with app.app_context():
        challenge1 = Challenge(
            user_id=sample_user.id,
            challenge_type="fitness",
            difficulty="easy",
            mindset_type="Warrior",
        )
        challenge2 = Challenge(
            user_id=sample_user.id,
            challenge_type="study",
            difficulty="hard",
            mindset_type="Sage",
        )
        db.session.add(challenge1)
        db.session.commit()
        # Small delay to ensure different timestamps
        import time
        time.sleep(0.1)
        db.session.add(challenge2)
        db.session.commit()

    # Login and check dashboard
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    response = client.get("/dashboard")
    assert response.status_code == 200
    # The latest challenge (study) should be displayed
    assert b"Study" in response.data or b"study" in response.data.lower()


# ============================================
# TASK COMPLETION & XP TESTS
# ============================================

def test_complete_task_awards_xp(client, sample_user, app):
    """Test that completing a task awards XP."""
    # Create a task
    task = Task(
        user_id=sample_user.id,
        title="Learn new concept",
        stat_category="INT",
    )

    with app.app_context():
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    # Login and complete task
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    response = client.post(
        f"/complete-task/{task_id}",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"earned" in response.data or b"XP" in response.data

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.progress.xp == 10
        assert user.progress.intelligence_xp == 10


def test_complete_task_updates_correct_stat(client, sample_user, app):
    """Test that completing a task updates the correct stat category."""
    # Create tasks for each stat
    stat_categories = {
        "STR": "strength_xp",
        "INT": "intelligence_xp",
        "SPI": "spirituality_xp",
        "VIT": "vitality_xp",
        "CHA": "charisma_xp",
    }

    for stat_code, stat_field in stat_categories.items():
        task = Task(
            user_id=sample_user.id,
            title=f"Test {stat_code} task",
            stat_category=stat_code,
        )

        with app.app_context():
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        # Login and complete task
        client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "password123",
            },
        )

        client.post(f"/complete-task/{task_id}")

        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            stat_value = getattr(user.progress, stat_field)
            assert stat_value >= 10

        # Logout for next iteration
        client.get("/logout")


def test_complete_task_triggers_level_up(client, sample_user, app):
    """Test that completing enough tasks triggers a level up."""
    with app.app_context():
        # Create 10 tasks (100 XP total = level up from 1 to 2)
        for i in range(10):
            task = Task(
                user_id=sample_user.id,
                title=f"Task {i}",
                stat_category="STR",
            )
            db.session.add(task)
        db.session.commit()

        tasks = Task.query.filter_by(user_id=sample_user.id).all()
        task_ids = [t.id for t in tasks]

    # Login
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # Complete all tasks
    for task_id in task_ids:
        client.post(f"/complete-task/{task_id}")

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.progress.xp >= 100
        assert user.progress.level == 2


def test_complete_same_task_twice_only_awards_xp_once(client, sample_user, app):
    """Test that completing the same task twice only awards XP once."""
    task = Task(
        user_id=sample_user.id,
        title="One-time task",
        stat_category="INT",
    )

    with app.app_context():
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    # Login
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # Complete task first time
    response1 = client.post(f"/complete-task/{task_id}", follow_redirects=True)
    assert b"earned" in response1.data or b"XP" in response1.data

    # Try to complete task second time
    response2 = client.post(f"/complete-task/{task_id}", follow_redirects=True)
    assert b"already completed" in response2.data

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        # Should still be only 10 XP (not 20)
        assert user.progress.xp == 10


# ============================================
# COMMUNITY PRIVACY TESTS
# ============================================

def test_community_shows_only_public_users(client, app):
    """Test that community page only shows users with is_public=True."""
    # Create public and private users
    with app.app_context():
        public_user = User(username="publicwarrior", email="public@example.com")
        public_user.set_password("password123")
        public_user.is_public = True
        public_progress = Progress(user=public_user)

        private_user = User(username="privatewarrior", email="private@example.com")
        private_user.set_password("password123")
        private_user.is_public = False
        private_progress = Progress(user=private_user)

        db.session.add(public_user)
        db.session.add(public_progress)
        db.session.add(private_user)
        db.session.add(private_progress)
        db.session.commit()

    # Login as public user
    client.post(
        "/login",
        data={
            "username": "publicwarrior",
            "password": "password123",
        },
    )

    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    assert b"publicwarrior" in response.data
    assert b"privatewarrior" not in response.data


def test_user_can_toggle_public_status(client, sample_user, app):
    """Test that user can toggle their public status."""
    # Login
    client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123",
        },
    )

    # Save challenge with is_public checked (set to public)
    client.post(
        "/dashboard",
        data={
            "challenge_type": "fitness",
            "difficulty": "easy",
            "mindset_type": "Warrior",
            "is_public": "on",
            "save_challenge": "on",
        },
    )

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.is_public is True

    # Save challenge without is_public (set to private)
    client.post(
        "/dashboard",
        data={
            "challenge_type": "fitness",
            "difficulty": "easy",
            "mindset_type": "Warrior",
            "save_challenge": "on",
        },
    )

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.is_public is False


def test_community_page_requires_login(client):
    """Test that community page requires authentication."""
    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data or b"log in" in response.data


def test_multiple_public_users_all_shown(client, app):
    """Test that all public users are shown on community page."""
    with app.app_context():
        # Create 5 public users
        for i in range(5):
            user = User(username=f"user{i}", email=f"user{i}@example.com")
            user.set_password("password123")
            user.is_public = True
            progress = Progress(user=user)
            db.session.add(user)
            db.session.add(progress)
        db.session.commit()

    # Login as first user
    client.post(
        "/login",
        data={
            "username": "user0",
            "password": "password123",
        },
    )

    response = client.get("/community", follow_redirects=True)

    assert response.status_code == 200
    # Check that multiple users are shown
    for i in range(1, 5):
        assert f"user{i}".encode() in response.data


# ============================================
# LEVEL CALCULATION TESTS
# ============================================

def test_level_calculation_from_xp(app):
    """Test that level is correctly calculated from XP."""
    assert calculate_level_from_xp(0) == 1
    assert calculate_level_from_xp(50) == 1
    assert calculate_level_from_xp(99) == 1
    assert calculate_level_from_xp(100) == 2
    assert calculate_level_from_xp(199) == 2
    assert calculate_level_from_xp(200) == 3
    assert calculate_level_from_xp(1000) == 11

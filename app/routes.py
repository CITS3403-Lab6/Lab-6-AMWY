from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.constants import VALID_CHALLENGE_TYPES, VALID_DIFFICULTIES, VALID_MINDSET_TYPES
from app.constants import MAX_TASK_TITLE_LENGTH, TASK_XP_REWARD
from app.forms import ChallengeForm, LoginForm, ReflectionForm, SignupForm
from app.models import Challenge, Task, User
from app.services import (
    add_accountability_partner,
    apply_daily_hp_result,
    build_dashboard_data,
    calculate_circle_score,
    complete_user_task,
    create_reflection,
    get_accountability_partner_cards,
    get_or_create_progress,
    get_public_users,
    remove_accountability_partner,
)

main = Blueprint("main", __name__)


@main.route("/")
def home():
    """Render the home page."""
    return render_template("home.html")


@main.route("/signup", methods=["GET", "POST"])
def signup():
    """Register a new user and create their progress record."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = SignupForm()

    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            get_or_create_progress(user)

            login_user(user)
            flash("Account created successfully.", "success")
            return redirect(url_for("main.dashboard"))

        except IntegrityError:
            db.session.rollback()
            flash("Username or email already exists.", "error")
        except Exception:
            db.session.rollback()
            flash("An unexpected error occurred during signup.", "error")

    return render_template("signup.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    """Log in an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(form.password.data):
            get_or_create_progress(user)
            login_user(user)
            flash("Logged in successfully.", "success")

            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html", form=form)


@main.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))



@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """Show dashboard and handle challenge saving."""
    progress = get_or_create_progress(current_user)
    challenge_form = ChallengeForm()

    if request.method == "POST" and request.form.get("save_challenge"):
        challenge_type = (request.form.get("challenge_type") or "").strip()
        difficulty = (request.form.get("difficulty") or "").strip().lower()
        mindset_type = (request.form.get("mindset_type") or "").strip()

        if (
            challenge_type not in VALID_CHALLENGE_TYPES
            or difficulty not in VALID_DIFFICULTIES
            or mindset_type not in VALID_MINDSET_TYPES
        ):
            flash("Invalid challenge data.", "error")
            return redirect(url_for("main.dashboard"))

        try:
            current_user.is_public = bool(request.form.get("is_public"))

            challenge = Challenge(
                user_id=current_user.id,
                challenge_type=challenge_type,
                difficulty=difficulty,
                mindset_type=mindset_type,
            )

            db.session.add(challenge)
            db.session.commit()

            flash("Challenge saved successfully.", "success")
            return redirect(url_for("main.dashboard"))

        except Exception:
            db.session.rollback()
            flash("Could not save challenge. Please try again.", "error")
            return redirect(url_for("main.dashboard"))

    latest_challenge = current_user.latest_challenge()

    tasks = (
        Task.query
        .filter_by(user_id=current_user.id, task_date=date.today())
        .order_by(Task.completed.asc(), Task.created_at.desc())
        .all()
    )

    dashboard_data = build_dashboard_data(current_user)
    if not isinstance(dashboard_data, dict):
        dashboard_data = {}

    dashboard_data.setdefault("hp", getattr(progress, "hp", 100))
    dashboard_data.setdefault("max_hp", getattr(progress, "max_hp", 100))
    dashboard_data.setdefault("xp", getattr(progress, "xp", 0))
    dashboard_data.setdefault("level", getattr(progress, "level", 1))
    dashboard_data.setdefault("streak", getattr(progress, "streak", 0))

    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.completed)
    completion_percentage = round((completed_tasks / total_tasks) * 100) if total_tasks else 0

    dashboard_data.setdefault("total_tasks", total_tasks)
    dashboard_data.setdefault("completed_tasks", completed_tasks)
    dashboard_data.setdefault("completion_percentage", completion_percentage)

    dashboard_data.setdefault(
        "difficulty",
        latest_challenge.difficulty if latest_challenge else "medium",
    )
    dashboard_data.setdefault(
        "difficulty_target",
        {"easy": 50, "medium": 70, "hard": 90}.get(dashboard_data["difficulty"], 70),
    )
    dashboard_data.setdefault(
        "current_challenge",
        latest_challenge.challenge_type if latest_challenge else None,
    )
    dashboard_data.setdefault("character_reveal_stage", min(10, dashboard_data["level"] // 10))

    dashboard_data.setdefault(
        "progress",
        {
            "hp": dashboard_data["hp"],
            "max_hp": dashboard_data["max_hp"],
            "xp": dashboard_data["xp"],
            "level": dashboard_data["level"],
            "streak": dashboard_data["streak"],
            "completion_percentage": dashboard_data["completion_percentage"],
        },
    )

    dashboard_data.setdefault(
        "tasks_today",
        {
            "total": total_tasks,
            "completed": completed_tasks,
            "completion_percentage": completion_percentage,
        },
    )

    dashboard_data.setdefault(
        "character",
        {
            "stage": dashboard_data["character_reveal_stage"],
            "name": f"Stage {dashboard_data['character_reveal_stage']}",
            "description": "Your character is revealed as you level up.",
        },
    )

    template_context = dict(dashboard_data)
    template_context.pop("progress", None)
    template_context.pop("tasks", None)
    template_context.pop("challenge", None)

    reflection_form = ReflectionForm()

    return render_template(
        "dashboard.html",
        challenge_form=challenge_form,
        reflection_form=reflection_form,
        challenge=latest_challenge,
        tasks=tasks,
        progress=progress,
        dashboard_data=dashboard_data,
        **template_context,
    )


@main.route("/challenge", methods=["GET"])
@login_required
def challenge_setup():
    """Render challenge/difficulty setup page."""
    challenge_form = ChallengeForm()
    return render_template("challenge_setup.html", challenge_form=challenge_form)


@main.route("/add-task", methods=["POST"])
@login_required
def add_task():
    """Add a daily task for the current user."""
    title = request.form.get("title", "").strip()
    stat_category = request.form.get("stat_category", "VIT").strip() or "VIT"

    if not title:
        flash("Task title is required.", "error")
        return redirect(url_for("main.dashboard"))

    if len(title) > MAX_TASK_TITLE_LENGTH:
        flash("Task title must be under 200 characters.", "error")
        return redirect(url_for("main.dashboard"))

    try:
        task = Task(
            user_id=current_user.id,
            title=title,
            stat_category=stat_category,
        )

        db.session.add(task)
        db.session.commit()

        flash("Task added successfully.", "success")

    except IntegrityError:
        db.session.rollback()
        flash("Invalid task data.", "error")
    except Exception:
        db.session.rollback()
        flash("Could not add task. Please try again.", "error")

    return redirect(url_for("main.dashboard"))


@main.route("/complete-task/<int:task_id>", methods=["POST"])
@login_required
def complete_task(task_id):
    """Complete a task and award XP."""
    task = db.session.get(Task, task_id)

    if task is None:
        flash("Task not found.", "error")
        return redirect(url_for("main.dashboard"))

    try:
        completed_now, levelled_up = complete_user_task(current_user, task)

        if completed_now:
            flash(f"Task completed! You earned {TASK_XP_REWARD} XP.", "success")

            if levelled_up:
                flash(
                    f"Level up! You are now level {current_user.progress.level}.",
                    "success",
                )
        else:
            flash("Task was already completed.", "info")

    except PermissionError:
        db.session.rollback()
        flash("You cannot modify another user's task.", "error")
    except ValueError:
        db.session.rollback()
        flash("Could not complete task because progress data is invalid.", "error")
    except Exception:
        db.session.rollback()
        flash("Could not complete task. Please try again.", "error")

    return redirect(url_for("main.dashboard"))


@main.route("/reflection", methods=["POST"])
@login_required
def reflection():
    """Save a daily reflection."""
    form = ReflectionForm()

    if not form.validate_on_submit():
        flash("Reflection was not saved because the form was invalid.", "error")
        return redirect(url_for("main.dashboard"))

    try:
        create_reflection(
            user=current_user,
            mood=form.mood.data,
            note=form.note.data,
        )

        flash("Reflection saved successfully.", "success")

    except ValueError as error:
        db.session.rollback()
        flash(str(error), "error")
    except Exception:
        db.session.rollback()
        flash("Could not save reflection. Please try again.", "error")

    return redirect(url_for("main.dashboard"))



@main.route("/community")
@login_required
def community():
    """Show public users and accountability circle data."""
    try:
        public_users = get_public_users()
    except TypeError:
        public_users = get_public_users(None)

    partner_cards = []
    circle_score = 0

    try:
        partner_cards = get_accountability_partner_cards(current_user)
        circle_score = calculate_circle_score(current_user)
    except Exception:
        partner_cards = []
        circle_score = 0

    return render_template(
        "community.html",
        users=public_users,
        public_users=public_users,
        partners=partner_cards,
        partner_cards=partner_cards,
        circle_score=circle_score,
    )


@main.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Render and update account/privacy settings."""
    if request.method == "POST":
        privacy_value = (
            request.form.get("privacy")
            or request.form.get("is_public")
            or ""
        ).strip().lower()

        current_user.is_public = privacy_value in {
            "public",
            "true",
            "1",
            "yes",
            "on",
        }

        try:
            db.session.commit()

            if current_user.is_public:
                flash("Your progress is now public in the community page.", "success")
            else:
                flash("Your progress is now private.", "success")

        except Exception:
            db.session.rollback()
            flash("Could not update privacy settings.", "error")

        return redirect(url_for("main.settings"))

    return render_template("settings.html")


@main.route("/evaluate-day", methods=["POST"])
@login_required
def evaluate_day():
    """Evaluate today's completion and apply HP damage or streak gain."""
    progress = get_or_create_progress(current_user)
    today = date.today()

    if getattr(progress, "last_evaluated_date", None) == today:
        flash("Today has already been evaluated.", "info")
        return redirect(url_for("main.dashboard"))

    dashboard_data = build_dashboard_data(current_user)
    completion_percentage = dashboard_data.get("completion_percentage", 0)
    difficulty = dashboard_data.get("difficulty", None)

    try:
        result = apply_daily_hp_result(
            progress=progress,
            completion_percentage=completion_percentage,
            difficulty=difficulty,
        )

        progress.last_evaluated_date = today
        db.session.commit()

        if result["met_target"]:
            flash("Daily target met. Streak increased.", "success")
        else:
            flash(f"Daily target missed. HP reduced by {result['hp_lost']}.", "warning")

    except Exception:
        db.session.rollback()
        flash("Could not evaluate today. Please try again.", "error")

    return redirect(url_for("main.dashboard"))


@main.route("/community/add-partner", methods=["POST"])
@main.route("/community/partners/add", methods=["POST"])
@main.route("/add-partner", methods=["POST"])
@login_required
def add_partner():
    """Add a public user to the current user's accountability circle."""
    identifier = (
        request.form.get("partner_identifier")
        or request.form.get("partner_username")
        or request.form.get("partner_email")
        or request.form.get("username")
        or request.form.get("email")
        or request.form.get("user_identifier")
        or ""
    ).strip()

    try:
        partner_link = add_accountability_partner(current_user, identifier)
        flash(
            f"{partner_link.partner.username} added to your accountability circle.",
            "success",
        )
    except ValueError as exc:
        flash(str(exc), "error")
    except Exception:
        db.session.rollback()
        flash("Could not add accountability partner. Please try again.", "error")

    return redirect(url_for("main.community"))


@main.route("/community/remove-partner/<int:partner_id>", methods=["POST"])
@main.route("/community/partners/<int:partner_id>/remove", methods=["POST"])
@main.route("/remove-partner/<int:partner_id>", methods=["POST"])
@login_required
def remove_partner(partner_id):
    """Remove a user from the current user's accountability circle."""
    try:
        remove_accountability_partner(current_user, partner_id)
        flash("Accountability partner removed.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    except Exception:
        db.session.rollback()
        flash("Could not remove accountability partner. Please try again.", "error")

    return redirect(url_for("main.community"))
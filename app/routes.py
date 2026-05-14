from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from datetime import date
from app import db
from app.constants import (
    MAX_TASK_TITLE_LENGTH,
    TASK_XP_REWARD,
)
from app.forms import ChallengeForm, LoginForm, ReflectionForm, SignupForm
from app.models import Challenge, Task, User
from app.services import (
    build_dashboard_data,
    complete_user_task,
    create_reflection,
    get_dashboard_data,
    get_or_create_progress,
    get_public_users,
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

    #to remove
    reflection_form = ReflectionForm()

    if challenge_form.validate_on_submit() and request.form.get("save_challenge"):
        try:
            current_user.is_public = bool(challenge_form.is_public.data)

            challenge = Challenge(
                user_id=current_user.id,
                mindset_type=challenge_form.mindset_type.data,
            )

            db.session.add(challenge)
            db.session.commit()

            flash("Challenge started successfully.", "success")
            return redirect(url_for("main.dashboard"))

        except IntegrityError:
            db.session.rollback()
            flash("Invalid challenge data.", "error")
        except Exception:
            db.session.rollback()
            flash("Could not save challenge. Please try again.", "error")
    
    dashboard_data = get_dashboard_data(current_user)

    tasks = (
        Task.query
        .filter_by(user_id=current_user.id, task_date=date.today())
        .order_by(Task.completed.asc(), Task.created_at.desc())
        .all()
    )

    dashboard_data = build_dashboard_data(current_user)

    return render_template(
        "dashboard.html",
        dashboard_data=dashboard_data,
        challenge_form=challenge_form,
        challenge=current_user.latest_challenge(),
        reflection_form=reflection_form,
        tasks=tasks,
        progress=progress,
        dashboard_data=dashboard_data,
    )


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
                flash(f"Level up! You are now level {current_user.progress.level}.", "success")
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
    """Show public user progress."""
    public_users = get_public_users()
    return render_template("community.html", public_users=public_users)

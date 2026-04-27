from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User, Challenge, Task, Progress, Reflection
from app.forms import SignupForm, LoginForm, ChallengeForm, ReflectionForm

main = Blueprint("main", __name__)


@main.route("/")
def home():
    """Home page"""
    return render_template("home.html")


@main.route("/signup", methods=["GET", "POST"])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    
    form = SignupForm()
    if form.validate_on_submit():
        try:
            # Create user
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            # Create associated progress
            progress = Progress(user=user)
            
            db.session.add(user)
            db.session.add(progress)
            db.session.commit()
            
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("main.login"))
        
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already exists. Please try again.", "error")
            return redirect(url_for("main.signup"))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during signup. Please try again.", "error")
    
    return render_template("signup.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password.", "error")
    
    return render_template("login.html", form=form)


@main.route("/logout")
@login_required
def logout():
    """User logout"""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """User dashboard with challenge and task management"""
    challenge_form = ChallengeForm()
    reflection_form = ReflectionForm()
    
    # Handle challenge submission
    if challenge_form.validate_on_submit() and request.form.get("save_challenge"):
        try:
            current_user.is_public = challenge_form.is_public.data
            
            challenge = Challenge(
                user_id=current_user.id,
                challenge_type=challenge_form.challenge_type.data,
                difficulty=challenge_form.difficulty.data,
                mindset_type=challenge_form.mindset_type.data,
            )
            
            db.session.add(challenge)
            db.session.commit()
            flash("Challenge saved successfully.", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Error saving challenge. Please try again.", "error")
    
    # Fetch user data
    latest_challenge = Challenge.query.filter_by(user_id=current_user.id)\
        .order_by(Challenge.created_at.desc()).first()
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        "dashboard.html",
        challenge_form=challenge_form,
        reflection_form=reflection_form,
        challenge=latest_challenge,
        tasks=tasks,
        progress=current_user.progress,
    )


@main.route("/add-task", methods=["POST"])
@login_required
def add_task():
    """Add a new task"""
    title = request.form.get("title", "").strip()
    stat_category = request.form.get("stat_category", "").strip()
    
    if not title or not stat_category:
        flash("Task title and category are required.", "error")
        return redirect(url_for("main.dashboard"))
    
    if len(title) > 200:
        flash("Task title must be under 200 characters.", "error")
        return redirect(url_for("main.dashboard"))
    
    valid_categories = ["STR", "INT", "SPI", "VIT", "CHA"]
    if stat_category not in valid_categories:
        flash("Invalid stat category.", "error")
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
    except Exception as e:
        db.session.rollback()
        flash("Error adding task. Please try again.", "error")
    
    return redirect(url_for("main.dashboard"))


@main.route("/complete-task/<int:task_id>", methods=["POST"])
@login_required
def complete_task(task_id):
    """Mark a task as complete"""
    task = Task.query.get_or_404(task_id)
    
    # Access control
    if task.user_id != current_user.id:
        flash("You cannot modify another user's task.", "error")
        return redirect(url_for("main.dashboard"))
    
    try:
        if not task.completed:
            task.completed = True
            
            progress = current_user.progress
            xp_gain = 10
            progress.xp += xp_gain
            
            # Award category-specific XP
            if task.stat_category == "STR":
                progress.strength_xp += xp_gain
            elif task.stat_category == "INT":
                progress.intelligence_xp += xp_gain
            elif task.stat_category == "SPI":
                progress.spirituality_xp += xp_gain
            elif task.stat_category == "VIT":
                progress.vitality_xp += xp_gain
            elif task.stat_category == "CHA":
                progress.charisma_xp += xp_gain
            
            # Check for level up
            leveled_up = False
            while progress.xp >= progress.level * 100:
                progress.level += 1
                leveled_up = True
            if leveled_up:
                flash(f"Level up! You are now level {progress.level}!", "success")
            
            db.session.commit()
            flash(f"Task completed! You earned {xp_gain} XP.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error completing task. Please try again.", "error")
    
    return redirect(url_for("main.dashboard"))


@main.route("/reflection", methods=["POST"])
@login_required
def reflection():
    """Save daily reflection"""
    form = ReflectionForm()
    
    if form.validate_on_submit():
        try:
            reflection = Reflection(
                user_id=current_user.id,
                mood=form.mood.data,
                note=form.note.data,
            )
            db.session.add(reflection)
            db.session.commit()
            flash("Reflection saved successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error saving reflection. Please try again.", "error")
    
    return redirect(url_for("main.dashboard"))


@main.route("/community")
@login_required
def community():
    """Community page showing public user progress"""
    public_users = User.query.filter_by(is_public=True).all()
    return render_template("community.html", public_users=public_users)
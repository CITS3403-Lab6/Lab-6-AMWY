from datetime import datetime, date, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


def utc_now():
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    """Registered HabitWise user."""

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_public = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    challenges = db.relationship(
        "Challenge",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    tasks = db.relationship(
        "Task",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    progress = db.relationship(
        "Progress",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    reflections = db.relationship(
        "Reflection",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def latest_challenge(self):
        return (
            Challenge.query
            .filter_by(user_id=self.id)
            .order_by(Challenge.created_at.desc(), Challenge.id.desc())
            .first()
        )

    def __repr__(self):
        return f"<User {self.username}>"


class Challenge(db.Model):
    """A user's selected mindset challenge."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )

    mindset_type = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)

    __table_args__ = (
        db.CheckConstraint(
            "mindset_type IN ('Sage', 'Warrior', 'Demon')",
            name="valid_mindset_type",
        ),
    )

    def __repr__(self):
        return f"<Challenge {self.mindset_type}>"


class Task(db.Model):
    """Daily user task."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(200), nullable=False)

    completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    task_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def __repr__(self):
        return f"<Task {self.title}>"


class Progress(db.Model):
    """A user's RPG-style progress record."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    level = db.Column(db.Integer, default=1, nullable=False)
    xp = db.Column(db.Integer, default=0, nullable=False)
    streak = db.Column(db.Integer, default=0, nullable=False)
    last_evaluated_date = db.Column(db.Date, nullable=True)

    hp = db.Column(db.Integer, default=100, nullable=False)
    max_hp = db.Column(db.Integer, default=100, nullable=False)

    updated_at = db.Column(
        db.DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (
        db.CheckConstraint("level >= 1", name="progress_level_minimum"),
        db.CheckConstraint("level <= 100", name="progress_level_cap"),
        db.CheckConstraint("xp >= 0", name="progress_xp_non_negative"),
        db.CheckConstraint("streak >= 0", name="progress_streak_non_negative"),
        db.CheckConstraint("hp >= 0 AND hp <= max_hp", name="progress_hp_range"),
        db.CheckConstraint("max_hp > 0", name="progress_max_hp_positive"),
    )

    def __repr__(self):
        return f"<Progress user_id={self.user_id} level={self.level} xp={self.xp}>"


class Reflection(db.Model):
    """A user's daily reflection entry."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )

    mood = db.Column(db.String(50), nullable=True)
    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)

    def __repr__(self):
        return f"<Reflection user_id={self.user_id} created_at={self.created_at}>"

class AccountabilityPartner(db.Model):
    """A user-selected accountability partner relationship."""

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    partner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    owner = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref("accountability_partners", cascade="all, delete-orphan"),
    )

    partner = db.relationship(
        "User",
        foreign_keys=[partner_id],
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "partner_id",
            name="unique_accountability_partner",
        ),
        db.CheckConstraint(
            "user_id != partner_id",
            name="cannot_add_self_as_accountability_partner",
        ),
    )

    def __repr__(self):
        return f"<AccountabilityPartner user={self.user_id} partner={self.partner_id}>"


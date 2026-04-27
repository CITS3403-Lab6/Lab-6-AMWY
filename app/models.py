from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model, UserMixin):
    """User model with authentication"""
    id = db.Column(db.Integer, primary_key=True)
    
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    challenges = db.relationship("Challenge", backref="user", lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship("Task", backref="user", lazy=True, cascade="all, delete-orphan")
    progress = db.relationship("Progress", backref="user", uselist=False, cascade="all, delete-orphan")
    reflections = db.relationship("Reflection", backref="user", lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"


class Challenge(db.Model):
    """Challenge model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    
    challenge_type = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(30), nullable=False)
    mindset_type = db.Column(db.String(30), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<Challenge {self.challenge_type}>"


class Task(db.Model):
    """Task model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    
    title = db.Column(db.String(200), nullable=False)
    stat_category = db.Column(db.String(10), nullable=False)
    
    completed = db.Column(db.Boolean, default=False, index=True)
    task_date = db.Column(db.Date, default=date.today, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Task {self.title}>"


class Progress(db.Model):
    """Progress tracking model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True, index=True)
    
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    
    strength_xp = db.Column(db.Integer, default=0)
    intelligence_xp = db.Column(db.Integer, default=0)
    spirituality_xp = db.Column(db.Integer, default=0)
    vitality_xp = db.Column(db.Integer, default=0)
    charisma_xp = db.Column(db.Integer, default=0)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Progress Level {self.level}>"


class Reflection(db.Model):
    """Daily reflection model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    
    mood = db.Column(db.String(50), nullable=True)
    note = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<Reflection {self.created_at}>"
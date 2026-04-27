from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models import User


class SignupForm(FlaskForm):
    """User registration form"""
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=80, message="Username must be 3-80 characters")
        ]
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Invalid email address")
        ]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters")
        ]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match")
        ]
    )
    submit = SubmitField("Create Account")
    
    def validate_username(self, field):
        """Check if username already exists"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken.")
    
    def validate_email(self, field):
        """Check if email already exists"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField(
        "Username",
        validators=[DataRequired()]
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )
    submit = SubmitField("Login")


class ChallengeForm(FlaskForm):
    """Challenge creation form"""
    challenge_type = SelectField(
        "Challenge Type",
        choices=[
            ("fitness", "Fitness"),
            ("study", "Study"),
            ("meditation", "Meditation"),
            ("creativity", "Creativity"),
            ("nutrition", "Nutrition"),
        ],
        validators=[DataRequired()]
    )
    difficulty = SelectField(
        "Difficulty",
        choices=[
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
        ],
        validators=[DataRequired()]
    )
    mindset_type = SelectField(
        "Mindset Type",
        choices=[
            ("Sage", "Sage - Think & Reflect"),
            ("Warrior", "Warrior - Act & Execute"),
            ("Demon", "Demon - Embrace Chaos"),
        ],
        validators=[DataRequired()]
    )
    is_public = BooleanField("Share progress publicly")
    submit = SubmitField("Save Challenge")


class ReflectionForm(FlaskForm):
    """Daily reflection form"""
    mood = SelectField(
        "Mood",
        choices=[
            ("great", "Great 😊"),
            ("good", "Good 🙂"),
            ("okay", "Okay 😐"),
            ("bad", "Bad ☹️"),
            ("terrible", "Terrible 😠"),
        ],
        validators=[Optional()]
    )
    note = TextAreaField(
        "Reflection",
        validators=[
            Optional(),
            Length(max=1000, message="Reflection must be under 1000 characters")
        ]
    )
    submit = SubmitField("Save Reflection")
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError,
)

from app.constants import (
    MAX_EMAIL_LENGTH,
    MAX_PASSWORD_MIN_LENGTH,
    MAX_REFLECTION_LENGTH,
    MAX_USERNAME_LENGTH,
    VALID_MINDSET_TYPES,
)
from app.models import User


class SignupForm(FlaskForm):
    """User registration form."""

    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(
                min=3,
                max=MAX_USERNAME_LENGTH,
                message="Username must be 3-80 characters.",
            ),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Invalid email address."),
            Length(max=MAX_EMAIL_LENGTH),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(
                min=MAX_PASSWORD_MIN_LENGTH,
                message="Password must be at least 6 characters.",
            ),
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )

    submit = SubmitField("Create Account")

    def validate_username(self, field):
        username = field.data.strip()

        if User.query.filter_by(username=username).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        email = field.data.strip().lower()

        if User.query.filter_by(email=email).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    """User login form."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ChallengeForm(FlaskForm):
    """Challenge creation form."""

    mindset_type = SelectField(
        "Challenge/difficulty Type",
        choices=[(key, value["name"]) for key, value in VALID_MINDSET_TYPES.items()],
        validators=[DataRequired()],
    )

    is_public = BooleanField("Share progress publicly")
    submit = SubmitField("Start Challenge")

#To remove feature
class ReflectionForm(FlaskForm):
    """Daily reflection form."""

    mood = SelectField(
        "Mood",
        choices=[
            ("great", "Great 😊"),
            ("good", "Good 🙂"),
            ("okay", "Okay 😐"),
            ("bad", "Bad ☹️"),
            ("terrible", "Terrible 😠"),
        ],
        validators=[Optional()],
    )

    note = TextAreaField(
        "Reflection",
        validators=[
            Optional(),
            Length(
                max=MAX_REFLECTION_LENGTH,
                message="Reflection must be under 1000 characters.",
            ),
        ],
    )

    submit = SubmitField("Save Reflection")

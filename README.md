# HabitWise - Mindset-Based Habit Tracking

HabitWise is a gamified habit-tracking web application that combines personal development with community accountability. Users select mindset archetypes (Sage, Warrior, or Demon) to frame their daily challenges, earn XP and level up, and optionally share their progress with a public community.

## MVP Features

### Core Features
- **User Authentication**: Secure signup and login with password hashing and CSRF protection
- **Mindset-Based Challenges**: Select from three challenge types (Sage, Warrior, Demon) that align with different personas and goals
- **Daily Task Management**: Create and track daily tasks with completion status
- **Progress Tracking**: HP and XP system with levels and streaks
- **Dashboard**: Personalized view of current challenge, tasks, progress, and stats

### Community & Accountability
- **Public Profiles**: Optional public profile sharing to build accountability
- **Community Discovery**: Browse other users' public profiles and achievements
- **Accountability Partners**: Connect with other users for mutual support
- **Reflection Mechanism**: Write daily reflections on progress toward goals

### Privacy & Security
- **Privacy Controls**: Toggle public/private profile visibility
- **CSRF Protection**: All forms protected against cross-site request forgery
- **Secure Password Storage**: Passwords hashed using Werkzeug security

### Gamification
- **HP/XP System**: Gain XP from tasks, lose HP from missed daily challenges
- **Streaks**: Track consecutive days of challenge engagement
- **Levels**: Progression based on accumulated XP
- **Character Archetypes**: Three mindset types with distinct mechanics

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Lab-6-AMWY
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # or
   source venv/bin/activate       # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database** (creates tables and loads demo users)
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://localhost:5000`

### Useful Commands

**Reset the database** (clears all data and reinitializes with demo users)
```bash
python init_db.py
```

**Run the test suite** (all tests)
```bash
pytest
```

**Run specific test file**
```bash
pytest tests/test_authentication_flow.py
```

**Run tests with verbose output**
```bash
pytest -v
```

**Run tests and generate coverage report**
```bash
pytest --cov=app
```

## Demo Accounts

The database initializes with three demo accounts for testing. Use these credentials to explore the application:

| Username | Email | Password | Profile Type | Challenge |
|----------|-------|----------|--------------|-----------|
| `demo_public` | demo_public@example.com | `Password123!` | Public | Study (Medium) |
| `demo_private` | demo_private@example.com | `Password123!` | Private | Fitness (Easy) |
| `demo_partner` | demo_partner@example.com | `Password123!` | Public | Creativity (Hard) |

**Note**: These accounts are recreated when you run `python init_db.py`, so any modifications will be lost.

## Project Structure

```
├── app/                          # Application package
│   ├── __init__.py              # App factory and extensions
│   ├── config.py                # Configuration settings
│   ├── constants.py             # Application constants
│   ├── forms.py                 # WTForms forms
│   ├── models.py                # SQLAlchemy models
│   ├── routes.py                # Flask route handlers
│   ├── services.py              # Business logic
│   ├── templates/               # HTML templates
│   └── instance/                # Instance-specific files (DB)
├── static/                       # Static assets
│   ├── css/                      # Stylesheets
│   ├── js/                       # JavaScript files
│   └── img/                      # Images and sprites
├── tests/                        # Test suite
├── init_db.py                    # Database initialization script
├── run.py                        # Application entry point
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
└── README.md                     # This file
```

## Technology Stack

- **Backend**: Flask 2.3.3, SQLAlchemy 3.0.5
- **Authentication**: Flask-Login 0.6.3
- **Forms**: Flask-WTF 1.3.0, WTForms 3.0.1
- **Database**: SQLite (configured in Flask-SQLAlchemy)
- **Testing**: Pytest 7.4.0, Selenium 4.11.2
- **Security**: Werkzeug 2.3.7, CSRF protection

## Troubleshooting

### Database Issues
If you encounter database errors, reset the database:
```bash
rm instance/habitwise.db  # Remove old database
python init_db.py         # Reinitialize with fresh data
```

### Port Already in Use
If port 5000 is already in use, modify [app/run.py](app/run.py) or set the Flask port:
```bash
set FLASK_ENV=development  # Windows
set FLASK_PORT=5001
python run.py
```

### Missing Dependencies
Reinstall all dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

## Development Notes

- The application runs in debug mode by default (enables auto-reload and interactive debugger)
- Demo data is created automatically when `init_db.py` is run
- All database files are stored in the `instance/` directory
- Static files are served from the `static/` directory

## Testing

The test suite covers:
- Authentication and security (CSRF protection, password hashing)
- User model functionality
- Route handlers and views
- Community features (accountability partners, public profiles)
- Privacy settings
- Task and progress mechanics
- Error handling

Run the full test suite:
```bash
pytest
```

For detailed test results:
```bash
pytest -v --tb=short
```
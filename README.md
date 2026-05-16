# HabitWise - Mindset-Based Habit Tracking

HabitWise is a gamified habit-tracking web application that helps users build discipline through daily tasks, HP/XP progression, mindset-based challenges, reflections, and community accountability.

Users can create an account, select a mindset mode, manage daily tasks, earn XP, protect their HP, build streaks, reveal a character through level progress, and optionally share their progress with public community members.

---

## Group Members

| UWA ID   | Name         | GitHub Username |
|--------  |------        |-----------------|
| 24261709 | Yuvraj Singh | yuvraj-sk |
| 24160091 | Advay Katoch | kotchadon |
| 24830144 | Woojin Song  | wjin2006 |
| 24239793 | Michael Kartika | mrdudman |



---

## Main Features

### Authentication
- User signup, login, and logout
- Passwords stored securely using hashed passwords
- Protected dashboard, settings, and community pages

### Dashboard
- Add and complete daily tasks
- Earn XP when tasks are completed
- Level up based on accumulated XP
- View HP, XP, level, streak, daily target, and completion percentage
- View weekly progress calculated from task completion
- Character reveal progress based on user level
- Save daily reflections
- View recent previous reflections

### Mindset Challenge System
Users can choose one of three mindset modes:

| Mode | Daily Target | Description |
|------|--------------|-------------|
| Sage | 50% | Balanced and sustainable |
| Warrior | 70% | Disciplined and consistent |
| Demon | 90% | High-intensity challenge mode |

The selected mode controls the daily completion percentage required to avoid HP loss.

### HP, XP, Level, and Streaks
- Completing tasks gives XP
- XP increases user level
- Character reveal progresses with level
- Evaluating the day compares task completion against the selected daily target
- Meeting the daily target increases streak
- Missing the daily target reduces HP and resets streak

### Community and Accountability
- Users can make their profile public or private
- Public users appear in the community page
- Private users are hidden from community discovery
- Users can add/remove public users as accountability partners
- Partner cards show progress information such as streak, level, XP, HP, and current mode

### Privacy and Security
- Public/private profile visibility setting
- CSRF protection on POST forms
- Secure password hashing
- Flask configuration separated from application logic

---

## Technology Stack

- HTML
- CSS
- JavaScript
- Flask
- Jinja templates
- Flask-Login
- Flask-WTF / WTForms
- Flask-SQLAlchemy
- SQLite
- Pytest
- Selenium

---

## Project Structure

```text
Lab-6-AMWY/
├── app/
│   ├── __init__.py          # Flask app factory and extensions
│   ├── config.py            # App configuration
│   ├── constants.py         # Shared constants and game rules
│   ├── forms.py             # Flask-WTF forms
│   ├── models.py            # SQLAlchemy database models
│   ├── routes.py            # Flask route handlers
│   ├── services.py          # Business logic
│   └── templates/           # Jinja HTML templates
├── static/
│   ├── css/                 # CSS files
│   ├── js/                  # JavaScript files
│   └── img/                 # Images and visual assets
├── tests/                   # Unit and Selenium tests
├── init_db.py               # Database reset and demo data script
├── run.py                   # Application runner
├── requirements.txt         # Python dependencies
├── pytest.ini               # Pytest configuration
└── README.md
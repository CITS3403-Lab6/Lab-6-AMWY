# HabitWise - Mindset-Based Habit Tracking

HabitWise is a gamified habit-tracking web application that helps users build discipline through daily tasks, HP/XP progression, mindset-based challenges, reflections, character reveal progress, HabitWise Oracle recommendations, and community accountability.

Users can create an account, choose a mindset mode, manage daily tasks, earn XP, protect HP, build streaks, save reflections, and connect with accountability partners.

---

## Purpose

HabitWise makes habit tracking more engaging by turning daily discipline into a game-like system.

The app helps users stay consistent through:

- Daily tasks
- HP, XP, levels, and streaks
- Mindset modes: Sage, Warrior, and Demon
- Character reveal progression
- Daily reflections
- HabitWise Oracle recommendations
- Public/private community accountability

---

## Features

### Authentication

- User signup, login, and logout
- Passwords stored securely using hashed passwords
- Protected dashboard, settings, challenge, and community pages

### Dashboard

- Add and complete daily tasks
- Earn XP when tasks are completed
- View HP, XP, level, streak, daily target, and completion percentage
- View weekly progress
- Reveal a character through progress
- Save and view previous reflections
- Evaluate the day against the selected mindset target

### HabitWise Oracle

HabitWise includes an Oracle panel on the dashboard.

The Oracle reads the user's current data, including tasks, completion percentage, HP, streak, level, selected mindset mode, and remaining tasks. It then gives a short progress summary, risk status, and practical recommendations.

The Oracle changes tone based on the selected mode:

| Mode | Oracle Style |
|------|--------------|
| Sage | Calm and reflective |
| Warrior | Direct and disciplined |
| Demon | Intense and high-pressure |

The HabitWise Oracle is deterministic and backend-driven. It does not use an external AI API.

### Mindset Modes

| Mode | Daily Target | Description |
|------|--------------|-------------|
| Sage | 50% | Balanced and sustainable |
| Warrior | 70% | Disciplined and consistent |
| Demon | 90% | High-intensity challenge mode |

The selected mode controls the daily completion target needed to avoid HP loss.

### Progress System

- Completing tasks gives XP
- XP increases the user's level
- Character reveal progress increases with user progress
- Meeting the daily target increases streak
- Missing the daily target reduces HP and resets streak
- Progress data is stored persistently

### Community and Accountability

- Users can make their profile public or private
- Public users appear in the Community page
- Private users are hidden from public discovery
- Users can add and remove accountability partners
- Partner cards show streak, level, XP, HP, current mode, and activity status
- Already-added partners are filtered from the add-partner list

### Activity Visibility

- Users can choose whether their online/activity status is visible
- Online or hidden status is shown using activity dots in the Community page
- Activity visibility can be changed from Settings

### Privacy and Security

- Public/private community visibility
- CSRF protection on POST forms
- Hashed passwords
- Protected routes requiring login
- Users cannot modify another user's tasks
- Security headers and hardened session cookie settings

---

## Team Members

| UWA ID | Name | GitHub Username |
|--------|------|-----------------|
| 24261709 | Yuvraj Singh | yuvraj-sk |
| 24160091 | Advay Katoch | kotchadon |
| 24830144 | Woojin Song | wjin2006 |
| 24239793 | Michael Kartika | mrdudman |

---

## Technologies Used

| Area | Technologies |
|------|--------------|
| Backend | Flask, Flask-Login, Flask-WTF, Flask-SQLAlchemy |
| Frontend | HTML, CSS, JavaScript, Jinja templates |
| Database | SQLite, SQLAlchemy ORM |
| Security | Werkzeug password hashing, CSRF protection, security headers |
| Testing | Pytest, Selenium |

---

## How to Launch

### Prerequisites

- Python 3.10+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/CITS3403-Lab6/Lab-6-AMWY.git
cd Lab-6-AMWY
```

### 2. Create a virtual environment

Windows:

```powershell
py -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

Windows:

```powershell
py -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m pip install -r requirements.txt
```

### 4. Initialise/reset the database

Windows:

```powershell
py init_db.py
```

macOS/Linux:

```bash
python3 init_db.py
```

### 5. Run the application

Windows:

```powershell
py run.py
```

macOS/Linux:

```bash
python3 run.py
```

Open the app at:

```text
http://127.0.0.1:5000
```

or:

```text
http://localhost:5000
```

---

## Main Commands

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Reset/init database:

```powershell
py init_db.py
```

Run app:

```powershell
py run.py
```

Run all tests:

```powershell
py -m pytest -q
```

Run tests with detailed output:

```powershell
py -m pytest -v
```

Run a specific test file:

```powershell
py -m pytest tests/test_authentication_flow.py
```

---

## Demo Accounts

Running `init_db.py` creates demo users.

Demo login details:

| Username | Email | Password | Purpose |
|----------|-------|----------|---------|
| demo_public | demo_public@example.com | Password123! | Public demo user |
| demo_private | demo_private@example.com | Password123! | Private demo user |
| will_campbell | will.campbell@example.com | Password123! | Public community user |
| emily_clarke | emily.clarke@example.com | Password123! | Public community user |
| noah_nguyen | noah.nguyen@example.com | Password123! | Public community user |
| mia_anderson | mia.anderson@example.com | Password123! | Public community user |

Demo data is reset every time `init_db.py` is run.

---

## How to Run Tests

The project uses Pytest and Selenium.

Run the full test suite:

```powershell
py -m pytest -q
```

Expected final result:

```text
127 passed
```

The test suite covers:

- Authentication
- Password security
- CSRF protection
- Security headers
- Database models
- Routes
- Dashboard functionality
- HabitWise Oracle logic
- Task completion
- HP, XP, level, and streak logic
- Reflection saving and display
- Settings privacy
- Activity visibility
- Community visibility
- Accountability partners
- Selenium user flows

---

## Manual Demo Flow

1. Run `py init_db.py`
2. Run `py run.py`
3. Log in as `demo_public`
4. Open the Dashboard
5. Check the HabitWise Oracle panel
6. Add and complete a task
7. Check XP, level, and character reveal progress
8. Save a reflection
9. Open previous reflections
10. Click Evaluate Today
11. Check HP and streak behaviour
12. Go to Settings
13. Toggle community visibility
14. Change activity visibility
15. Go to Community
16. Add and remove an accountability partner
17. Log out

To test two users, use one normal browser window and one incognito/private window.

---

## Database

The app uses SQLite with SQLAlchemy.

The database is created/reset with:

```powershell
py init_db.py
```

Main models:

| Model | Purpose |
|-------|---------|
| User | Account, login, privacy, and activity visibility |
| Progress | HP, XP, level, streak, and daily evaluation data |
| Task | Daily tasks |
| Challenge | Selected mindset mode |
| Reflection | Mood and reflection notes |
| AccountabilityPartner | Partner links between users |

---

## Security

HabitWise includes:

- Hashed passwords using Werkzeug
- CSRF protection through Flask-WTF
- CSRF tokens on POST forms
- Login-required protected pages
- Public/private profile visibility
- Activity visibility controls
- Security headers
- Hardened session and remember-me cookie settings

---

## Current Status

HabitWise meets the core project requirements:

- Client-server web application
- User signup, login, and logout
- Persistent user data
- Public community/accountability features
- Server-side Flask routes and database models
- HTML, CSS, JavaScript, and Jinja frontend
- Automated unit and Selenium testing
- CSRF protection and secure password handling
- HabitWise Oracle smart recommendation panel
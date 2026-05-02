# Flask/Jinja Template Migration Guide

## Summary of Changes

This document outlines the conversion of the frontend from a single-page application (index.html) to proper Flask/Jinja templates.

## Directory Structure

```
HabitWise/
├── app/
│   ├── __init__.py
│   ├── forms.py            # WTForms forms (already set up)
│   ├── models.py           # SQLAlchemy models (already set up)
│   ├── routes.py           # Flask routes (already set up)
│   └── templates/
│       ├── base.html       # ✅ Updated - Base template with navigation
│       ├── home.html       # ✅ Updated - Enhanced with RPG theme
│       ├── signup.html     # ✅ Updated - Better styling
│       ├── login.html      # ✅ Updated - Better styling
│       ├── dashboard.html  # ✅ Updated - RPG-themed dashboard
│       ├── community.html  # ✅ Updated - Public leaderboard
│       └── challenge_setup.html  # ✅ New - Challenge intro page
├── static/
│   ├── css/
│   │   └── style.css       # ✅ Updated - Merged with RPG theme
│   ├── js/
│   │   └── script.js       # ✅ Created - Client-side interactions
│   └── img/                # ✅ Created (needs image files moved here)
│       ├── backgrounds/
│       └── titles/
└── [root files: index.html, style.css, script.js - can be deleted]
```

## Key Changes

### 1. CSS Updates (`static/css/style.css`)

- ✅ Merged old `style.css` with modern Flask styling
- ✅ Added RPG pixel theme elements:
  - Press Start 2P font family
  - Green (#22c55e) accent color scheme
  - Pixel-art borders (2px instead of 1px, no border-radius)
  - Text shadows for RPG aesthetic
  - Box shadows with pixel effect
- ✅ Updated button styles with pixel art effect
- ✅ Enhanced form styling with RPG borders
- ✅ Added animations for title fade and transitions

### 2. Templates

#### base.html
- ✅ Updated navigation with user authentication state
- ✅ Added links: Home, Dashboard, Community, (Logout for authenticated users)
- ✅ Shows username for logged-in users
- ✅ Better brand with ⚔ symbols
- ✅ Includes background layer for RPG theme
- ✅ Message flash display with proper styling

#### home.html
- ✅ Enhanced hero section with RPG theme
- ✅ Added "How It Works" section
- ✅ Added stat system explanation
- ✅ Call-to-action section
- ✅ Better copy with RPG language

#### signup.html & login.html
- ✅ Updated with RPG titles ("Make The Oath", "Welcome Back")
- ✅ Better form styling with pixel theme
- ✅ Warning icons (⚠) for error messages
- ✅ Better placeholders

#### dashboard.html
- ✅ RPG-themed header (⚔ Your Dashboard ⚔)
- ✅ Enhanced stat display with emoji indicators
- ✅ Better challenge info section
- ✅ Task category icons (⚔ STR, 🧠 INT, ✨ SPI, ❤️ VIT, 💬 CHA)
- ✅ Improved task completion UI
- ✅ Better reflection form styling

#### community.html
- ✅ RPG-themed header
- ✅ Enhanced user cards with better stat display
- ✅ Proper formatting for leaderboard view
- ✅ User warrior icons (⚔)

#### challenge_setup.html (NEW)
- ✅ Challenge selection interface
- ✅ Difficulty level selector
- ✅ Mindset chooser (Sage, Warrior, Demon)
- ✅ Educational descriptions for each option

### 3. JavaScript (`static/js/script.js`)

- ✅ Created new static JavaScript file
- ✅ Random background image selection
- ✅ Button ripple effect on click
- ✅ Form submission feedback
- ✅ Console greeting with HabitWise branding

## Image Files

The background and title images are already stored under `/static/img/` in the current repository structure.

Current image structure in `/static/img/`:
- backgrounds/: origbig.png, origbig2.png, origbig3.png, origbig4.png
- titles/: habitwise_01_lava.png, habitwise_02_water.png, etc.
- Other: Bat-IdleFly.png, orig.png

## Flask Integration

### Routes Available
- `GET  /` → home.html
- `GET  /signup` → signup.html
- `POST /signup` → User registration
- `GET  /login` → login.html
- `POST /login` → User authentication
- `GET  /logout` → Logout user
- `GET  /dashboard` → dashboard.html (requires login)
- `POST /dashboard` → Create/update challenge
- `POST /add-task` → Add new task
- `POST /complete-task/<id>` → Mark task as complete
- `POST /reflection` → Save daily reflection
- `GET  /community` → community.html (requires login)

### Database Models
- **User**: Username, email, password_hash, is_public flag
- **Challenge**: Type, difficulty, mindset, created_at
- **Task**: Title, stat_category, completed, task_date
- **Progress**: Level, XP, streak, stat-specific XP
- **Reflection**: Mood, note, created_at

## Form Validation

All forms use WTForms with built-in validation:
- **SignupForm**: Username availability, email format, password matching
- **LoginForm**: Simple username/password fields
- **ChallengeForm**: Dropdown selections for type, difficulty, mindset
- **ReflectionForm**: Mood selection, optional note

## Data Flow

### User Registration
1. User fills signup form
2. Form validates (no duplicates, password match)
3. User created in database with hashed password
4. Progress record auto-created
5. Redirect to login

### User Login
1. User fills login form
2. Username/password verified
3. Session created (flask-login)
4. Redirect to dashboard

### Challenge Creation
1. User selects challenge type, difficulty, mindset
2. Challenge record created in database
3. linked to current user
4. User can create daily tasks

### Task Completion
1. User marks task as complete
2. XP awarded based on stat category
3. Progress updated
4. Level-up check performed
5. User notified of XP gain

## Future Enhancements

- [ ] Move images to static/img/
- [ ] Add image compression/optimization
- [ ] Add streak tracking logic
- [ ] Add daily reset logic for tasks
- [ ] Implement reflection retrieval/history
- [ ] Add public profile pages
- [ ] Add social features (follows, comments)
- [ ] Add achievement/badge system
- [ ] Implement email verification
- [ ] Add password reset functionality

## Clean-up - Files to Remove

The following files from the root directory can be safely deleted:
- `index.html` (replaced by templates)
- `script.js` (moved to static/js/)
- `style.css` (merged into static/css/)
- `auth.html`, `auth.js`, `auth.css` (old auth files)
- `challenge.html`, `challenge.js`, `challenge.css` (old challenge files)
- `community.html`, `community.js`, `community.css` (old community files)
- `dashboard.html`, `dashboard.js`, `dashboard.css` (old dashboard files)
- `landing.html`, `landing.js`, `landing.css` (old landing files)
- `settings.html`, `settings.js`, `settings.css` (old settings files)

## Deployment Notes

1. Ensure Flask is running with templates from `app/templates/`
2. Static files are served from `static/` directory
3. Images should be in `static/img/` subdirectories
4. Database migrations may be needed for any model changes
5. Environment variables (.env) must be configured for production

## Browser Compatibility

- ✅ Modern browsers (Chrome, Firefox, Safari, Edge)
- ✅ CSS Grid and Flexbox support required
- ✅ JavaScript ES6+ features used
- ✅ No IE11 support (intentional - focusing on modern dev)

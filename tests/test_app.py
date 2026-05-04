import pytest

from app import create_app, db
from app.models import User, Progress, Challenge, Task


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def create_user(username='tester', email='tester@example.com', password='password'):
    user = User(username=username, email=email)
    user.set_password(password)
    progress = Progress(user=user)
    db.session.add_all([user, progress])
    db.session.commit()
    return user


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_signup_login_logout(client):
    # Signup
    res = client.post('/signup', data={
        'username': 'alice',
        'email': 'alice@example.com',
        'password': 'securepw',
        'confirm_password': 'securepw'
    }, follow_redirects=True)
    assert b'Account created successfully' in res.data or res.status_code in (200, 302)

    # Login
    res = client.post('/login', data={'username': 'alice', 'password': 'securepw'}, follow_redirects=True)
    assert b'Dashboard' in res.data or b'Your Dashboard' in res.data

    # Logout
    res = client.get('/logout', follow_redirects=True)
    assert b'logged out' in res.data.lower() or b'You have been logged out' in res.data


def test_model_creation_and_challenge_save(client, app):
    with app.app_context():
        user = create_user('bob', 'bob@example.com', 'pw')
        user_id = user.id

    # Login
    login(client, 'bob', 'pw')

    # Save challenge
    res = client.post('/dashboard', data={
        'challenge_type': 'fitness',
        'difficulty': 'easy',
        'mindset_type': 'Sage',
        'is_public': 'y',
        'save_challenge': 'save_challenge'
    }, follow_redirects=True)
    assert b'Challenge saved successfully' in res.data

    with app.app_context():
        ch = Challenge.query.filter_by(user_id=user_id).first()
        assert ch is not None
        assert ch.challenge_type == 'fitness'


def test_task_creation_and_completion_updates_xp(client, app):
    with app.app_context():
        user = create_user('carol', 'carol@example.com', 'pw')
        user_id = user.id
    login(client, 'carol', 'pw')

    # Add task
    res = client.post('/add-task', data={'title': 'Do pushups', 'stat_category': 'STR'}, follow_redirects=True)
    assert b'Task added successfully' in res.data

    with app.app_context():
        task = Task.query.filter_by(user_id=user_id).first()
        assert task is not None
        assert not task.completed

        # Complete task
        res = client.post(f'/complete-task/{task.id}', follow_redirects=True)
        assert b'Task completed' in res.data

        from app.models import Progress
        progress = Progress.query.filter_by(user_id=user_id).first()
        assert progress.xp >= 10
        assert progress.strength_xp >= 10


def test_community_shows_only_public_users(client, app):
    with app.app_context():
        u1 = create_user('public_user', 'pub@example.com', 'pw')
        u1.is_public = True
        u2 = create_user('private_user', 'priv@example.com', 'pw')
        u2.is_public = False
        db.session.commit()

    # Login as any user
    login(client, 'public_user', 'pw')
    res = client.get('/community')
    assert b'public_user' in res.data
    assert b'private_user' not in res.data

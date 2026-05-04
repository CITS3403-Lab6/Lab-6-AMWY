#!/usr/bin/env python
"""Initialize database"""
from app import create_app, db

app = create_app('development')
with app.app_context():
    db.create_all()
    print('Database initialized successfully')

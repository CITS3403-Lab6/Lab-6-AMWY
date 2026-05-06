from app import create_app, db

app = create_app("development")

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset and created successfully.")

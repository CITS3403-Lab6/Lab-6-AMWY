from app import create_app

app = create_app("development")

if __name__ == "__main__":
    app.run(debug=True)


from app import create_app, db
from app.models import Progress, User

app = create_app("development")
with app.app_context():
    user = User.query.filter_by(username="test_woojin").first()
    user.progress.level = 100
    user.progress.xp = 400
    db.session.commit()
    print("Done!")

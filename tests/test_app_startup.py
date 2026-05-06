from app import create_app, db


def test_app_factory_creates_app():
    app = create_app("testing")

    assert app is not None
    assert app.config["TESTING"] is True


def test_database_initialises_in_testing_mode():
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        table_names = db.metadata.tables.keys()

        assert "user" in table_names
        assert "task" in table_names
        assert "progress" in table_names
        assert "challenge" in table_names
        assert "reflection" in table_names


def test_home_route_runs_without_database_error(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"HabitWise" in response.data

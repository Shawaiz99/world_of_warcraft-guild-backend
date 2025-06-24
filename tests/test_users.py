import pytest
from flask import Flask
from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app("testing")  # Define "testing" config later
    app.config["TESTING"] = True
    # In-memory DB for fast tests
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_ping(client):
    res = client.get("/ping")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}

def test_user_registration(client):
    # Given
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "secure123"
    }

    # When
    res = client.post("/api/v1/register", json=user_data)

    # Then
    assert res.status_code == 201
    data = res.get_json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["role"] == "member"  # default role
    assert "id" in data
    assert "created_at" in data

import pytest
from app import app, socketio, active_users
from utils.validation import validate_subscription

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_valid_subscription():
    data = {"user_id": "user123", "type": "subscribe"}
    user_id = validate_subscription(data)
    assert user_id == "user123"

def test_invalid_subscription():
    with pytest.raises(ValueError):
        validate_subscription({"user_id": "", "type": "subscribe"})
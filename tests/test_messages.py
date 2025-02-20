import pytest
from app import app
from utils.validation import validate_message

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_valid_message():
    data = {"user_id": "user123", "type": "message", "payload": {"text": "Hello"}}
    user_id, message = validate_message(data)
    assert user_id == "user123"
    assert message == "Hello"

def test_invalid_message():
    with pytest.raises(ValueError):
        validate_message({"user_id": "user123", "type": "message", "payload": {}})
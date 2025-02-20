import pytest
from app import app, socketio, active_users
from unittest.mock import patch

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.mark.usefixtures("client")
@patch("openai.ChatCompletion.create")
def test_streaming_response(mock_openai):
    mock_openai.return_value = [
        {"choices": [{"delta": {"content": "Hello"}}]},
        {"choices": [{"delta": {"content": " World"}}]}
    ]
    # Create client without context manager
    client = socketio.test_client(app)

    # Perform test operations
    client.emit("subscribe", {"user_id": "user123", "type": "subscribe"})
    client.emit("message", {"user_id": "user123", "type": "message", "payload": {"text": "Hi"}})

    # Get and verify responses
    received = client.get_received()
    print(received)
    assert len(received) > 0
    assert received[0]["name"] == "subscription_ack"
    assert received[1]["name"] == "response_chunk"
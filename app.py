import os
from pathlib import Path

from flask import Flask, request
from flask_socketio import SocketIO, emit
import time
from dotenv import load_dotenv
from openai import OpenAI

from utils.event_handler import EventHandler

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

from utils.validation import validate_subscription, validate_message

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

client = OpenAI(api_key=os.getenv("OPENAPI_KEY"))

# Store active user connections
active_users = {}

@socketio.on("subscribe")
def handle_subscription(data):
    try:
        user_id = validate_subscription(data)
        active_users[user_id] = request.sid
        emit("subscription_ack", {
            "user_id": user_id,
            "type": "subscription_ack",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "payload": {"message": "Subscription successful"}
        })
    except Exception as e:
        emit("error", {
            "user_id": data.get("user_id"),
            "type": "error",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "payload": {"error": str(e)}
        })

@socketio.on("message")
def handle_message(data):
    try:
        # Validate the incoming message
        user_id, message = validate_message(data)

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )

        event_handler = EventHandler(user_id, socketio)

        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=os.getenv("OPENAPI_ASSISTANT_ID"),
            event_handler=event_handler
        ) as stream:
            stream.until_done()

    except Exception as e:
        print("e", e)
        emit("error", {
            "user_id": data.get("user_id"),
            "type": "error",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "payload": {"error": str(e)}
        })

@socketio.on("disconnect")
def handle_disconnect():
    user_id = None
    for uid, sid in active_users.items():
        if sid == request.sid:
            user_id = uid
            break
    if user_id:
        del active_users[user_id]
        print(f"User {user_id} disconnected")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
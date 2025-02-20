import os
from pathlib import Path

from flask import Flask, request
from flask_socketio import SocketIO, emit
import time
import openai
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

from utils.validation import validate_subscription, validate_message

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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

        # OpenAI API Key
        openai.api_key = os.getenv("OPENAPI_KEY")

        thread = openai.beta.threads.create()

        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=os.getenv("OPENAPI_ASSISTANT_ID"),
            instructions="Respond concisely and helpfully."
        )

        for event in openai.beta.threads.runs.stream(thread_id=thread.id, run_id=run.id):
            if event.event == "thread.message.delta":
                for content in event.data.delta.content:
                    if content.type == "text":
                        emit("response_chunk", {
                            "user_id": user_id,
                            "type": "response",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "payload": {"text_chunk": content.text.value}
                        })

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
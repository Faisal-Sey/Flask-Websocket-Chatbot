def validate_subscription(data):
    user_id = data.get("user_id")
    if not user_id:
        raise ValueError("Missing user_id")
    if data.get("type") != "subscribe":
        raise ValueError("Invalid subscription type")
    return user_id

def validate_message(data):
    user_id = data.get("user_id")
    if not user_id:
        raise ValueError("Missing user_id")
    if data.get("type") != "message":
        raise ValueError("Invalid message type")
    message = data.get("payload", {}).get("text")
    if not message:
        raise ValueError("Missing message text")
    return user_id, message
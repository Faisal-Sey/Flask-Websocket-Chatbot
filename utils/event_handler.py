import time

from typing_extensions import override

from openai import AssistantEventHandler


class EventHandler(AssistantEventHandler):
    def __init__(self, user_id, socketio):
        super().__init__()
        self.user_id = user_id
        self.socketio = socketio
        self.response_data = []

    @override
    def on_event(self, event):
        if event.event == 'thread.message.delta':
            print("content", event.data.delta.content)
            for content in event.data.delta.content:
                if content.type == "text":
                    self.response_data.append(content.text.value)
                    self.socketio.emit("response_chunk", {
                        "user_id": self.user_id,
                        "type": "response",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "payload": {"text_chunk": ' '.join(self.response_data)}
                    })
import json
from channels.generic.websocket import AsyncWebsocketConsumer

GROUP = "dispatch"

class DispatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(GROUP, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # клиент нам ничего не обязан слать; игнорируем
        pass

    # универсальный хендлер событий
    async def dispatch_event(self, event):
        # event = {"type": "dispatch.event", "payload": {...}}
        await self.send(text_data=json.dumps(event["payload"]))
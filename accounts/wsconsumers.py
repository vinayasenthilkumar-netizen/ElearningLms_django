
import json
from channels.generic.websocket import AsyncWebsocketConsumer


# websocket consumer that sends live notifications to the logged-in user
class NotificationConsumer(AsyncWebsocketConsumer):

    # runs when a websocket client tries to connect
    async def connect(self):

        user = self.scope["user"]

        # if the user is not logged in close the connection
        if not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{user.id}"

        # add this websocket connection to the user's group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # accept the websocket connection
        await self.accept()

    # runs when the websocket disconnects
    async def disconnect(self, close_code):
        # safely get the user from the scope
        user = self.scope.get("user")

        # only remove from the group if the user is valid and logged in
        if user and user.is_authenticated:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # runs when the server sends a notification_message event to the group
    async def notification_message(self, event):
        # send the notification data to the browser as json text
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "title": event["title"],
            "message": event["message"],
            "created_at": event["created_at"],
            "link": event["link"],
        }))
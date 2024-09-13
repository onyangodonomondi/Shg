# consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Increment user count when connected
        if not hasattr(self.channel_layer, 'user_count'):
            self.channel_layer.user_count = {}
        
        if self.room_group_name not in self.channel_layer.user_count:
            self.channel_layer.user_count[self.room_group_name] = 0

        self.channel_layer.user_count[self.room_group_name] += 1

        await self.accept()

        # Send the number of active users to all connected clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_user_count',
                'user_count': self.channel_layer.user_count[self.room_group_name],
            }
        )

    async def disconnect(self, close_code):
        # Decrement user count when disconnected
        self.channel_layer.user_count[self.room_group_name] -= 1

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Send the number of active users to all connected clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_user_count',
                'user_count': self.channel_layer.user_count[self.room_group_name],
            }
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    # Update user count
    async def update_user_count(self, event):
        user_count = event['user_count']

        # Send the user count to the WebSocket
        await self.send(text_data=json.dumps({
            'user_count': user_count
        }))

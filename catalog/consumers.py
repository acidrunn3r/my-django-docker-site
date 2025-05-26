import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class LikeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("likes_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("likes_group", self.channel_name)

    async def like_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'like_update',
            'image_id': event['image_id'],
            'likes_count': event['likes_count']
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'like_update':
            image_id = data['image_id']
            likes_count = await self.get_likes_count(image_id)
            
            await self.channel_layer.group_send(
                "likes_group",
                {
                    'type': 'like_message',
                    'image_id': image_id,
                    'likes_count': likes_count
                }
            )

    @database_sync_to_async
    def get_likes_count(self, image_id):
        from .models import Image
        image = Image.objects.get(id=image_id)
        return image.like_set.count()
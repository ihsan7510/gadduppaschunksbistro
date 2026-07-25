"""TV Display WebSocket Consumer"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TVDisplayConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('tv_display', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('tv_display', self.channel_name)

    async def receive(self, text_data):
        pass  # TV only receives updates

    async def order_update(self, event):
        """Called when any order status changes."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'table_number': event['table_number'],
            'status': event['status'],
        }))
    
    async def new_order(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'table_number': event['table_number'],
        }))

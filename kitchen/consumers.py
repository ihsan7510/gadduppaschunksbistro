"""Kitchen WebSocket Consumer"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class KitchenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('kitchen_orders', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('kitchen_orders', self.channel_name)

    async def receive(self, text_data):
        pass  # Kitchen only receives, doesn't send

    async def new_order(self, event):
        """Called when a new order is placed by a waiter."""
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'table_number': event['table_number'],
            'waiter': event.get('waiter', ''),
        }))
    
    async def order_update(self, event):
        """Called when order status changes."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'status': event['status'],
        }))

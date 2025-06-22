import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_str):
    try:
        token = AccessToken(token_str)
        user = User.objects.get(id=token.payload.get('user_id'))
        return user
    except Exception as e:
        print(f"Error getting user from token: {e}")
        return None

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("WebSocket connection attempt")
        try:
            # Получаем токен из query параметров
            query_string = parse_qs(self.scope['query_string'].decode())
            token = query_string.get('token', [None])[0]
            print(f"Got token: {token[:10]}...")  # Печатаем только начало токена для безопасности
            
            if not token:
                print("No token provided")
                await self.close()
                return
                
            # Получаем пользователя по токену
            user = await get_user_from_token(token)
            if not user:
                print("Invalid token or user not found")
                await self.close()
                return
                
            print(f"User authenticated: {user.id}")
            self.user_id = user.id
            self.group_name = f"user_{self.user_id}"
            
            # Присоединяемся к группе
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            print(f"Added to group: {self.group_name}")
            await self.accept()
            print("Connection accepted")
            
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        print(f"WebSocket disconnected with code: {close_code}")
        # Покидаем группу
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            print(f"Removed from group: {self.group_name}")
    
    async def notification_message(self, event):
        print(f"Sending notification: {event}")
        # Отправляем сообщение в WebSocket
        message = event["message"]
        await self.send(text_data=json.dumps({
            "type": "notification",
            "message": message
        })) 
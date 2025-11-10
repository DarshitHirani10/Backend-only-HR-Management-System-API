import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await self.get_user_from_token()
        if not self.user:
            logger.warning("WebSocket connection rejected: Invalid token or user not found")
            await self.close()
            return

        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send initial connection success and unread notifications count
        unread_count = await self.get_unread_notifications_count()
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": f"Connected as {self.user.username}",
            "unread_notifications": unread_count
        }))

        # Send recent notifications
        recent_notifications = await self.get_recent_notifications()
        if recent_notifications:
            await self.send(text_data=json.dumps({
                "type": "initial_notifications",
                "notifications": recent_notifications
            }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"WebSocket disconnected for user {self.user.id if hasattr(self, 'user') else 'unknown'}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get("command")
            
            if command == "mark_read":
                notification_id = data.get("notification_id")
                if notification_id:
                    success = await self.mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        "type": "notification_marked_read",
                        "success": success,
                        "notification_id": notification_id
                    }))
            elif command == "get_notifications":
                notifications = await self.get_recent_notifications()
                await self.send(text_data=json.dumps({
                    "type": "notifications_list",
                    "notifications": notifications
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Internal server error"
            }))

    async def notify(self, event):
        """Handle incoming notifications from the channel layer"""
        try:
            # Log receipt for debugging
            logger.info(f"notify received for user {getattr(self, 'user', None)}: {event}")
            await self.send(text_data=json.dumps(event["content"]))
            logger.info(f"notify sent to websocket for user {getattr(self, 'user', None)}")
        except Exception as e:
            logger.error(f"Error in notify: {str(e)}")

    @database_sync_to_async
    def get_user_from_token(self):
        """Authenticate user from the JWT token in query parameters"""
        try:
            query_string = self.scope["query_string"].decode()
            params = parse_qs(query_string)
            token = params.get("token", [None])[0]
            if not token:
                return None
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception as e:
            logger.error(f"Token authentication error: {str(e)}")
            return None

    @database_sync_to_async
    def get_unread_notifications_count(self):
        """Get count of unread notifications for the user"""
        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def get_recent_notifications(self):
        """Get recent notifications for the user"""
        notifications = Notification.objects.filter(user=self.user).order_by('-created_at')[:10]
        return [
            {
                "id": n.id,
                "message": n.message,
                "type": n.type,
                "created_at": n.created_at.isoformat(),
                "is_read": n.is_read
            }
            for n in notifications
        ]

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
            if not notification.is_read:
                notification.is_read = True
                notification.save()
            return True
        except Notification.DoesNotExist:
            return False

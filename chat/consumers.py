import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from chat.models import ChatRoom, Message

logger = logging.getLogger(__name__)

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # parse room name from the URL route kwargs
        self.room_name = self.scope['url_route']['kwargs'].get('room_name')
        if not self.room_name:
            logger.warning("No room_name in scope")
            await self.close(code=4001)
            return

        # authenticate user by token in query string with timeout
        try:
            self.user = await asyncio.wait_for(self.get_user_from_query(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.error("Timeout getting user from token")
            await self.close(code=4003)
            return
        
        if not self.user:
            logger.warning("User not found or token invalid")
            await self.close(code=4003)
            return

        # make group name deterministic
        self.group_name = f"chat_{self.room_name}"

        # verify user is participant with timeout
        try:
            allowed = await asyncio.wait_for(self.user_in_room(self.user, self.room_name), timeout=5.0)
        except asyncio.TimeoutError:
            logger.error("Timeout checking user in room")
            await self.close(code=4004)
            return
            
        if not allowed:
            logger.warning(f"User {self.user.id} not participant in room {self.room_name}")
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"WebSocket connected: user={self.user.id} room={self.room_name} channel={self.channel_name}")

        # optional: send joined notice
        await self.send(text_data=json.dumps({
            "type": "system",
            "message": f"Connected to {self.room_name} as {self.user.username}"
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"WebSocket disconnected: user={getattr(self,'user',None)} room={getattr(self,'room_name',None)}")

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data or "{}")
        except Exception:
            return

        action = payload.get("action")
        if action == "send_message":
            content = payload.get("content", "").strip()
            content_type = payload.get("content_type", "text")
            if not content:
                return
            # save message and broadcast
            msg = await self.create_message(room_name=self.room_name, sender=self.user, content=content, content_type=content_type)
            event = {
                "type": "chat_message",
                "message": {
                    "id": msg.id,
                    "room": msg.room.id,
                    "sender": self.user.username,
                    "content": msg.content,
                    "content_type": msg.content_type,
                    "created_at": msg.created_at.isoformat()
                }
            }
            try:
                await self.channel_layer.group_send(self.group_name, event)
                logger.info(f"Broadcasted message to group {self.group_name}: message_id={msg.id}")
            except Exception as e:
                logger.exception(f"Failed to broadcast message to group {self.group_name}: {e}")

    async def chat_message(self, event):
        """ Handler for chat messages sent to the group. """
        await self.send(text_data=json.dumps(event["message"]))


    @database_sync_to_async
    def get_user_from_query(self):
        logger.debug("DEBUG: get_user_from_query() called")
        qs = self.scope.get("query_string", b"").decode()
        logger.debug(f"DEBUG: query_string={qs}")
        params = parse_qs(qs)
        token = params.get("token", [None])[0]
        logger.debug(f"DEBUG: token extracted (len={len(token) if token else 0})")
        if not token:
            logger.debug("DEBUG: No token found in query string")
            return None
        try:
            logger.debug("DEBUG: About to parse AccessToken")
            access = AccessToken(token)
            logger.debug(f"DEBUG: AccessToken parsed, user_id={access.get('user_id')}")
            logger.debug("DEBUG: About to query User from DB")
            user = User.objects.get(id=access["user_id"])
            logger.debug(f"DEBUG: User found: {user.id}")
            return user
        except Exception as e:
            logger.exception(f"DEBUG: Exception in get_user_from_query: {e}")
            return None

    @database_sync_to_async
    def user_in_room(self, user, room_name):
        """
        Verify that the user is participant of the room (room_name is ChatRoom.name).
        """
        logger.debug(f"DEBUG: user_in_room() called with user={user.id} room={room_name}")
        try:
            logger.debug("DEBUG: About to query ChatRoom from DB")
            room = ChatRoom.objects.filter(name=room_name).first()
            logger.debug(f"DEBUG: ChatRoom query returned: {room}")
            if not room:
                logger.debug("DEBUG: Room not found")
                return False
            logger.debug("DEBUG: About to check participants")
            exists = room.participants.filter(id=user.id).exists()
            logger.debug(f"DEBUG: Participant check result: {exists}")
            return exists
        except Exception as e:
            logger.exception(f"DEBUG: Exception in user_in_room: {e}")
            return False

    @database_sync_to_async
    def create_message(self, room_name, sender, content, content_type="text"):
        room = ChatRoom.objects.filter(name=room_name).first()
        if not room:
            raise ValueError("Room not found")
        msg = Message.objects.create(room=room, sender=sender, content=content, content_type=content_type)
        return msg

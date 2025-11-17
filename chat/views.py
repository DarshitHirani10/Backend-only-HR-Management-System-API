from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from chat.models import ChatRoom, Message
from chat.serializers import ChatRoomSerializer, MessageSerializer
from accounts.models import Department, User
from django.shortcuts import get_object_or_404
from notifications.utils import notify_chat_group_added
import logging
import re

logger = logging.getLogger(__name__)

class CreatePrivateRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        other = request.data.get("other_username")
        if not other:
            return Response({"msg": "other_username required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other_user = User.objects.filter(username=other).first()
            if not other_user:
                return Response({"msg": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # deterministic key: sort numeric user ids to avoid lexical ordering issues
            participants = sorted([request.user.id, other_user.id])
            room_name = f"p_{participants[0]}_{participants[1]}"  # private room name

            room, created = ChatRoom.objects.get_or_create(name=room_name, defaults={"is_group": False, "title": f"{request.user.username} & {other_user.username}"})
            # ensure participants
            room.participants.add(request.user)
            room.participants.add(other_user)
            room.save()
            serializer = ChatRoomSerializer(room)
            return Response({"msg": "Private room ready", "data": serializer.data})
        except Exception as e:
            return Response({"msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateGroupRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group_name = request.data.get("group_name")
        title = request.data.get("title", "")
        usernames = request.data.get("usernames", [])

        if not group_name:
            return Response({"msg": "Group name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', group_name):
            return Response({
                "msg": "Group name can only contain letters, numbers, underscores (_), hyphens (-), or dots (.)"
            }, status=status.HTTP_400_BAD_REQUEST)
        if len(group_name) > 90:
            return Response({"msg": "Group name too long (max 90 characters)"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if ChatRoom.objects.filter(name=group_name).exists():
                return Response({"msg": "Group name already exists"}, status=status.HTTP_400_BAD_REQUEST)
            room = ChatRoom.objects.create(
                name=group_name,
                title=title or group_name,
                is_group=True
            )
            for uname in usernames:
                u = User.objects.filter(username=uname).first()
                if u:
                    room.participants.add(u)
                    # Notify user when added to group chat
                    try:
                        notify_chat_group_added(u, room.title, request.user)
                        logger.info(f"Chat group notification sent to {u.username} for group '{room.title}'")
                    except Exception as notif_error:
                        logger.exception(f"Failed to send chat group notification: {notif_error}")
            
            room.participants.add(request.user)
            room.save()
            serializer = ChatRoomSerializer(room)
            return Response({"msg": "Group created", "data": serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"msg": f"Error creating group: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

 
class ListRoomsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            rooms = request.user.chat_rooms.all().order_by('-created_at')
            serializer = ChatRoomSerializer(rooms, many=True)
            return Response({"msg": "Rooms fetched", "data": serializer.data})
        except Exception as e:
            return Response({"msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RoomMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        try:
            room = get_object_or_404(ChatRoom, id=room_id)
            # ensure user is participant
            if not room.participants.filter(id=request.user.id).exists():
                return Response({"msg": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
            messages = room.messages.all().order_by('created_at')
            serializer = MessageSerializer(messages, many=True)
            return Response({"msg": "Messages fetched", "data": serializer.data})
        except Exception as e:
            return Response({"msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SendMessageAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = get_object_or_404(ChatRoom, id=room_id)
            if not room.participants.filter(id=request.user.id).exists():
                return Response({"msg": "Not a participant"}, status=status.HTTP_403_FORBIDDEN)
            content = request.data.get("content", "")
            if not content:
                return Response({"msg": "content required"}, status=status.HTTP_400_BAD_REQUEST)

            msg = Message.objects.create(room=room, sender=request.user, content=content, content_type=request.data.get("content_type", "text"))

            # broadcast through channels layer
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            try:
                async_to_sync(channel_layer.group_send)(
                    f"chat_{room.name}",
                    {
                        "type": "chat_message",
                        "message": {
                            "id": msg.id,
                            "room": room.id,
                            "sender": request.user.username,
                            "content": msg.content,
                            "content_type": msg.content_type,
                            "created_at": msg.created_at.isoformat()
                        }
                    }
                )
                logger.info(f"Sent REST message broadcast to chat_{room.name} message_id={msg.id}")
            except Exception as e:
                logger.exception(f"Failed to broadcast via channel layer for chat_{room.name}: {e}")
            return Response({"msg": "Message sent", "data": MessageSerializer(msg).data})
        except Exception as e:
            return Response({"msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)

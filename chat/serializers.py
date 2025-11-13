from rest_framework import serializers
from chat.models import ChatRoom, Message
from accounts.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'content', 'content_type', 'created_at', 'is_system']
        read_only_fields = ['id', 'sender', 'created_at', 'is_system']

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.SlugRelatedField(many=True, slug_field='username', read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'title', 'is_group', 'department', 'participants', 'created_at', 'last_message']

    def get_last_message(self, obj):
        last = obj.messages.last()
        if not last:
            return None
        return {"sender": last.sender.username if last.sender else None, "content": last.content, "created_at": last.created_at.isoformat()}

from django.db import models
from django.utils import timezone
from hrms_backend.settings import AUTH_USER_MODEL
import uuid

User = AUTH_USER_MODEL

def default_room_name():
    return str(uuid.uuid4()).replace('-', '')[:16]

class ChatRoom(models.Model):
    """
    Chat room. If is_group is False -> one-to-one (private) chat.
    For one-to-one we create deterministic rooms (see manager in views).
    """
    name = models.CharField(max_length=255, unique=True, default=default_room_name)
    title = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    department = models.ForeignKey('accounts.Department', null=True, blank=True, on_delete=models.SET_NULL)
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title or self.name


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField()
    content_type = models.CharField(max_length=50, default='text')  # text, image, etc (future)
    created_at = models.DateTimeField(default=timezone.now)
    is_system = models.BooleanField(default=False)  # system messages (optional)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.content[:30]}"

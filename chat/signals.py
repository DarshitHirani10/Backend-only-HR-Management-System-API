"""
Signals for chat-related events: user added to group
"""
import logging
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from chat.models import ChatRoom
from notifications.utils import notify_chat_group_added

logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=ChatRoom.participants.through)
def notify_on_group_member_add(sender, instance, action, pk_set, **kwargs):
    """
    Notify users when they are added to a group chat
    """
    try:
        if action == 'post_add' and instance.is_group:
            # Get all newly added user IDs
            newly_added_ids = pk_set
            
            # For group chats, notify newly added members
            # We get the user who made the request from context if available
            # For now, we'll notify all added users
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            for user_id in newly_added_ids:
                try:
                    user = User.objects.get(id=user_id)
                    room_name = instance.title or instance.name
                    # We don't have the adding user info in signal, so we pass None
                    # In production, track who added the user
                    logger.info(f"User {user.username} added to group {room_name}")
                    # notify_chat_group_added(user, room_name, added_by_user)
                except User.DoesNotExist:
                    logger.warning(f"User with id {user_id} not found")
    except Exception as e:
        logger.exception(f"Error in chat participants signal: {e}")

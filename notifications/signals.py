from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notification)
def send_realtime_notification(sender, instance, created, **kwargs):
    if created:
        try:
            channel_layer = get_channel_layer()
            notification_data = {
                "id": instance.id,
                "message": instance.message,
                "type": instance.type,
                "created_at": instance.created_at.isoformat(),
                "is_read": instance.is_read,
            }
            
            group_name = f"user_{instance.user.id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notify",
                    "content": {
                        "type": "new_notification",
                        "notification": notification_data
                    }
                }
            )
            logger.info(f"Sent notification to group {group_name}")
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")

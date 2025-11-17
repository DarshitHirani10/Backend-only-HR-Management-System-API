import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from notifications.utils import notify_password_reset, notify_user_deleted, notify_profile_updated

logger = logging.getLogger(__name__)
User = get_user_model()

_user_original_values = {}

@receiver(pre_delete, sender=User)
def notify_before_user_deletion(sender, instance, **kwargs):
    try:
        logger.info(f"User deletion signal: {instance.username}")
    except Exception as e:
        logger.exception(f"Error in pre_delete signal: {e}")

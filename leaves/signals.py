import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from leaves.models import Leave
from notifications.utils import notify_leave_created, notify_leave_status

logger = logging.getLogger(__name__)

leave_original_status = {}


@receiver(pre_save, sender=Leave)
def store_leave_status(sender, instance, **kwargs):
    try:
        if instance.pk:
            old_instance = Leave.objects.get(pk=instance.pk)
            leave_original_status[instance.pk] = old_instance.status
    except Exception as e:
        logger.exception(f"Error storing leave status: {e}")


@receiver(post_save, sender=Leave)
def notify_on_leave_events(sender, instance, created, **kwargs):
    try:
        if created:
            logger.info(f"Leave created by {instance.user.username}")
            notify_leave_created(instance.user, instance.start_date, instance.end_date)
        else:
            old_status = leave_original_status.pop(instance.pk, None)
            if old_status and old_status != instance.status:
                logger.info(f"Leave status changed from {old_status} to {instance.status}")
                if instance.status in ['approved', 'rejected']:
                    notify_leave_status(instance.user, instance.status, None)
    except Exception as e:
        logger.exception(f"Error in leave signal: {e}")

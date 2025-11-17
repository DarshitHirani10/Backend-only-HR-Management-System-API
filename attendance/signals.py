import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from attendance.models import Attendance
from notifications.utils import notify_incomplete_shift

logger = logging.getLogger(__name__)

EXPECTED_HOURS = 8


@receiver(post_save, sender=Attendance)
def check_shift_completion(sender, instance, created, **kwargs):
    try:
        if not created and instance.check_out and instance.work_hours:
            logger.info(f"Shift completed for {instance.user.username}: {instance.work_hours} hours")
            if instance.work_hours < EXPECTED_HOURS:
                logger.warning(f"Incomplete shift for {instance.user.username}: {instance.work_hours}h < {EXPECTED_HOURS}h")
                notify_incomplete_shift(instance.user, instance.work_hours, EXPECTED_HOURS)
    except Exception as e:
        logger.exception(f"Error in attendance signal: {e}")

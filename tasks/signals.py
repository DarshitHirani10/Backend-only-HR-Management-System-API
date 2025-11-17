import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from tasks.models import Task
from notifications.utils import notify_task_assigned, notify_task_completed

logger = logging.getLogger(__name__)

task_original_status = {}


@receiver(pre_save, sender=Task)
def store_task_status(sender, instance, **kwargs):
    try:
        if instance.pk:
            old_instance = Task.objects.get(pk=instance.pk)
            task_original_status[instance.pk] = old_instance.status
    except Exception as e:
        logger.exception(f"Error storing task status: {e}")


@receiver(post_save, sender=Task)
def notify_on_task_events(sender, instance, created, **kwargs):
    try:
        if created:
            logger.info(f"Task created by {instance.created_by.username} and assigned to {instance.assigned_to.username}")
            notify_task_assigned(instance.assigned_to, instance.title, instance.created_by)
        else:
            old_status = task_original_status.pop(instance.pk, None)
            if old_status and old_status != instance.status:
                logger.info(f"Task status changed from {old_status} to {instance.status}")
                if instance.status == 'completed':
                    notify_task_completed(instance.created_by, instance.title, instance.assigned_to)
    except Exception as e:
        logger.exception(f"Error in task signal: {e}")

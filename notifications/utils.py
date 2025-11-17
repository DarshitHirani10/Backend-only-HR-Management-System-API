import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from notifications.models import Notification

logger = logging.getLogger(__name__)


def get_user_display_name(user):
    """
    Get user's display name (first_name + last_name or username)
    Handles None values safely
    """
    if user is None:
        return "System"
    if user.first_name or user.last_name:
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name if full_name else user.username
    return user.username


def send_email(subject, message, recipient_email, fail_silently=False):
    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)
        send_mail(subject, message, from_email, [recipient_email], fail_silently=fail_silently)
        logger.info(f"Email sent to {recipient_email}: {subject}")
    except Exception as e:
        logger.exception(f"Failed to send email to {recipient_email}: {e}")


def create_notification(user, message, notification_type, related_user=None, send_email_flag=False, email_subject=None, email_message=None):
    """
    Create a notification in DB and broadcast via WebSocket
    
    Args:
        user: User receiving the notification
        message: Notification message
        notification_type: Type of notification (choices from Notification.TYPE_CHOICES)
        related_user: User who performed the action (optional)
        send_email_flag: Whether to send email
        email_subject: Email subject (if send_email_flag=True)
        email_message: Email message (if send_email_flag=True)
    """
    try:
        # Create notification in DB
        notification = Notification.objects.create(
            user=user,
            message=message,
            type=notification_type,
            related_user=related_user
        )
        logger.info(f"Notification created for {user.username}: {notification_type}")
        
        # Broadcast via WebSocket
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "notify",
                    "message": message,
                    "notification_type": notification_type,
                    "notification_id": notification.id,
                }
            )
            logger.info(f"WebSocket notification sent to user_{user.id}")
        except Exception as ws_error:
            logger.warning(f"WebSocket broadcast failed: {ws_error}")
        
        # Send email if requested
        if send_email_flag and email_subject and email_message:
            send_email(email_subject, email_message, user.email)
        
        return notification
    except Exception as e:
        logger.exception(f"Error creating notification: {e}")
        return None


def notify_password_reset(user, admin_user):
    """
    Notify user that their password was reset by admin
    """
    message = f"Your password has been reset by {get_user_display_name(admin_user)}"
    email_subject = "Password Reset Notification"
    email_message = f"Your password has been reset by {get_user_display_name(admin_user)}. If this wasn't you, please contact support."
    
    create_notification(
        user=user,
        message=message,
        notification_type="password_reset",
        related_user=admin_user,
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


def notify_user_deleted(user, deleted_by_user):
    """
    Notify user that they were deleted by admin
    """
    message = f"Your account has been deleted by {get_user_display_name(deleted_by_user)}"
    email_subject = "Account Deleted Notification"
    email_message = f"Your account has been deleted by {get_user_display_name(deleted_by_user)}."
    
    create_notification(
        user=user,
        message=message,
        notification_type="user_deleted",
        related_user=deleted_by_user,
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


def notify_profile_updated(user, updated_by_user):
    """
    Notify user that their profile was updated
    """
    message = f"Your profile has been updated by {get_user_display_name(updated_by_user)}"
    email_subject = "Profile Update Notification"
    email_message = f"Your profile has been updated by {get_user_display_name(updated_by_user)}."
    
    create_notification(
        user=user,
        message=message,
        notification_type="profile",
        related_user=updated_by_user,
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


def notify_chat_group_added(user, group_name, added_by_user):
    """
    Notify user they were added to a chat group
    """
    message = f"You have been added to group '{group_name}' by {get_user_display_name(added_by_user)}"
    email_subject = "Added to Chat Group"
    email_message = f"You have been added to group '{group_name}' by {get_user_display_name(added_by_user)}."
    
    create_notification(
        user=user,
        message=message,
        notification_type="chat_group_added",
        related_user=added_by_user,
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


def notify_incomplete_shift(user, work_hours, expected_hours=8):
    """
    Notify user that their shift is incomplete
    """
    message = f"You have completed {work_hours} hours today. Expected shift: {expected_hours} hours."
    email_subject = "Incomplete Shift Notification"
    email_message = f"Your shift for today is incomplete. You worked {work_hours} hours, but the expected shift is {expected_hours} hours. Please contact your supervisor if this is an error."
    
    create_notification(
        user=user,
        message=message,
        notification_type="attendance",
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


def notify_leave_created(user, leave_start, leave_end):
    """
    Notify user's department seniors and admin about leave request
    """
    from accounts.models import User as UserModel
    
    message = f"Leave request from {get_user_display_name(user)} ({leave_start} to {leave_end})"
    email_subject = "Leave Request"
    email_message = f"New leave request from {get_user_display_name(user)}.\nFrom: {leave_start}\nTo: {leave_end}\nPlease review and approve/reject."
    
    # Notify all admins
    admins = UserModel.objects.filter(role__name="admin")
    for admin in admins:
        create_notification(
            user=admin,
            message=message,
            notification_type="leave",
            related_user=user,
            send_email_flag=True,
            email_subject=email_subject,
            email_message=email_message
        )
    
    # Notify department seniors
    if user.department:
        seniors = UserModel.objects.filter(department=user.department, role__name="senior")
        for senior in seniors:
            create_notification(
                user=senior,
                message=message,
                notification_type="leave",
                related_user=user,
                send_email_flag=True,
                email_subject=email_subject,
                email_message=email_message
            )


def notify_leave_status(user, status, approved_by_user):
    """
    Notify user about leave approval/rejection
    """
    message = f"Your leave has been {status} by {get_user_display_name(approved_by_user)}"
    email_subject = f"Leave {status.capitalize()}"
    email_message = f"Your leave has been {status} by {get_user_display_name(approved_by_user)}."
    
    create_notification(
        user=user,
        message=message,
        notification_type="leave",
        related_user=approved_by_user,
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


def notify_task_assigned(user, task_title, assigned_by_user):
    """
    Notify user that a task was assigned to them
    """
    message = f"Task '{task_title}' has been assigned to you by {get_user_display_name(assigned_by_user)}"
    email_subject = "Task Assigned"
    email_message = f"Task '{task_title}' has been assigned to you by {get_user_display_name(assigned_by_user)}."
    
    create_notification(
        user=user,
        message=message,
        notification_type="task",
        related_user=assigned_by_user,
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


def notify_task_completed(user, task_title, completed_by_user):
    """
    Notify task creator that assigned task is completed
    """
    message = f"Task '{task_title}' assigned to {get_user_display_name(completed_by_user)} has been completed. Please review."
    email_subject = "Task Completed - Review Required"
    email_message = f"Task '{task_title}' assigned to {get_user_display_name(completed_by_user)} has been completed. Please review it now."
    
    create_notification(
        user=user,
        message=message,
        notification_type="task",
        related_user=completed_by_user,
        send_email_flag=True,
        email_subject=email_subject,
        email_message=email_message
    )


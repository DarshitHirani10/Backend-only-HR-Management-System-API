from django.db import models
from django.utils import timezone
from accounts.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ("task", "Task"),
        ("profile", "Profile"),
        ("leave", "Leave"),
        ("password_reset", "Password Reset"),
        ("user_deleted", "User Deleted"),
        ("chat_group_added", "Chat Group Added"),
        ("attendance", "Attendance"),
        ("general", "General"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="general")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="initiated_notifications")  # who performed the action

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.type}"

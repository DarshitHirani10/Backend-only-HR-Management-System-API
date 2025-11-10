from django.db import models
from django.utils import timezone
from accounts.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ("task", "Task"),
        ("profile", "Profile"),
        ("leave", "Leave"),
        ("general", "General"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="general")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.type}"

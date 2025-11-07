from django.db import models
from django.utils import timezone
from accounts.models import User


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out:
            duration = self.check_out - self.check_in
            self.work_hours = round(duration.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

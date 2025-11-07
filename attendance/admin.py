from django.contrib import admin
from attendance.models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'check_in', 'check_out', 'work_hours')
    search_fields = ('user__username', 'date')
    list_filter = ('date',)

from django.contrib import admin
from tasks.models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_by', 'assigned_to', 'created_at')
    search_fields = ('title', 'created_by__username', 'assigned_to__username')
    list_filter = ('status',)

from django.contrib import admin
from leaves.models import Leave

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'start_date', 'end_date', 'applied_on')
    list_filter = ('status',)
    search_fields = ('user__username', 'reason')

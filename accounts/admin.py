from django.contrib import admin
from accounts.models import User, Role, Department, Designation

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "department", "is_active")
    search_fields = ("username", "email")

admin.site.register(Role)
admin.site.register(Department)
admin.site.register(Designation)
from rest_framework import serializers
from tasks.models import Task
from accounts.models import User

class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    assigned_to = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all()
    )

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'created_by', 'assigned_to', 'created_at', 'updated_at']

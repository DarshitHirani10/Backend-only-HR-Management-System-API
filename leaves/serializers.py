from rest_framework import serializers
from leaves.models import Leave


class LeaveSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Leave
        fields = ['id', 'user', 'start_date', 'end_date', 'reason', 'status', 'applied_on', 'updated_on']
        read_only_fields = ['status', 'applied_on', 'updated_on']

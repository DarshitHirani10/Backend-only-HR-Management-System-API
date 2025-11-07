from rest_framework import serializers
from attendance.models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'user', 'date', 'check_in', 'check_out', 'work_hours']

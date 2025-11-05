from rest_framework import serializers
from accounts.models import User, Role, Department, Designation

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']

class DesignationSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    class Meta:
        model = Designation
        fields = ['id', 'name', 'department']

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SlugRelatedField(slug_field='name', queryset=Role.objects.all(), required=False, allow_null=True)
    department = serializers.SlugRelatedField(slug_field='name', queryset=Department.objects.all(), required=False, allow_null=True)
    designation = serializers.SlugRelatedField(slug_field='name', queryset=Designation.objects.all(), required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'department', 'designation',
            'bio', 'phone', 'address'
        ]

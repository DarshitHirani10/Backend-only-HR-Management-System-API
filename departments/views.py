from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User, Role, Department, Designation
from departments.serializers import DepartmentSerializer, DesignationSerializer


def has_admin_access(user):
    if user.is_authenticated and user.role and user.role.name == "admin":
        return True
    return False



class DepartmentView(APIView):

    def get(self, request):
        try:
            departments = Department.objects.all()
            serializer = DepartmentSerializer(departments, many=True)
            return Response({"msg": "Departments fetched successfully", "data": serializer.data})
        except Exception as e:
            return Response({"msg": f"Error fetching departments: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            if not has_admin_access(request.user):
                return Response({"msg": "You do not have permission to create departments"}, status=status.HTTP_403_FORBIDDEN)
            serializer = DepartmentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"msg": "Department created successfully"})
            return Response({"msg": serializer.errors})
        except Exception as e:
            return Response({"msg": f"Error creating department: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            if not has_admin_access(request.user):
                return Response({"msg": "You do not have permission to update departments"}, status=status.HTTP_403_FORBIDDEN)
            department = Department.objects.filter(id=id).first()
            if not department:
                return Response({"msg": "Department not found"})
            serializer = DepartmentSerializer(department, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"msg": "Department updated successfully"})
            return Response({"msg": serializer.errors})
        except Exception as e:
            return Response({"msg": f"Error updating department: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            if not has_admin_access(request.user):
                return Response({"msg": "You do not have permission to delete departments"}, status=status.HTTP_403_FORBIDDEN)
            department = Department.objects.filter(id=id).first()
            if not department:
                return Response({"msg": "Department not found"})
            department.delete()
            return Response({"msg": "Department deleted successfully"})
        except Exception as e:
            return Response({"msg": f"Error deleting department: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class DesignationView(APIView):

    def get(self, request):
        try:
            designations = Designation.objects.select_related('department').all()
            serializer = DesignationSerializer(designations, many=True)
            return Response({"msg": "Designations fetched successfully", "data": serializer.data})
        except Exception as e:
            return Response({"msg": f"Error fetching designations: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            if not has_admin_access(request.user):
                return Response({"msg": "You do not have permission to create designations"}, status=status.HTTP_403_FORBIDDEN)
            serializer = DesignationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"msg": "Designation created successfully"})
            return Response({"msg": serializer.errors})
        except Exception as e:
            return Response({"msg": f"Error creating designation: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            if not has_admin_access(request.user):
                return Response({"msg": "You do not have permission to update designations"}, status=status.HTTP_403_FORBIDDEN)
            designation = Designation.objects.filter(id=id).first()
            if not designation:
                return Response({"msg": "Designation not found"})
            serializer = DesignationSerializer(designation, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"msg": "Designation updated successfully"})
            return Response({"msg": serializer.errors})
        except Exception as e:
            return Response({"msg": f"Error updating designation: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            if not has_admin_access(request.user):
                return Response({"msg": "You do not have permission to delete designations"}, status=status.HTTP_403_FORBIDDEN)
            designation = Designation.objects.filter(id=id).first()
            if not designation:
                return Response({"msg": "Designation not found"})
            designation.delete()
            return Response({"msg": "Designation deleted successfully"})
        except Exception as e:
            return Response({"msg": f"Error deleting designation: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

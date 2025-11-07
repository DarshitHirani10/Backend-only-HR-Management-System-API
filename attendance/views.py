from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from attendance.models import Attendance
from attendance.serializers import AttendanceSerializer
from accounts.models import User
from django.utils import timezone


def get_user_role(user):
    return user.role.name if user.role else None


class CheckInView(APIView):
    def post(self, request):
        try:
            user = request.user
            today = timezone.now().date()
            existing = Attendance.objects.filter(user=user, date=today).first()
            if existing:
                return Response({"msg": "Already checked in today"}, status=status.HTTP_400_BAD_REQUEST)
            Attendance.objects.create(user=user, check_in=timezone.now(), date=today)
            return Response({"msg": "Checked in successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error during check-in: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class CheckOutView(APIView):
    def post(self, request):
        try:
            user = request.user
            today = timezone.now().date()
            record = Attendance.objects.filter(user=user, date=today).first()
            if not record:
                return Response({"msg": "No check-in record found for today"}, status=status.HTTP_404_NOT_FOUND)
            if record.check_out:
                return Response({"msg": "Already checked out today"}, status=status.HTTP_400_BAD_REQUEST)
            record.check_out = timezone.now()
            record.save()
            return Response({"msg": "Checked out successfully", "hours": record.work_hours}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error during check-out: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class AttendanceListView(APIView):
    def get(self, request):
        try:
            user = request.user
            role = get_user_role(user)
            if role == "admin":
                records = Attendance.objects.all().order_by('-date')
            elif role == "senior":
                dept_users = User.objects.filter(department=user.department)
                records = Attendance.objects.filter(user__in=dept_users)
            elif role in ["junior", "intern"]:
                records = Attendance.objects.filter(user=user)
            else:
                return Response({"msg": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)
            serializer = AttendanceSerializer(records, many=True)
            return Response({"msg": "Attendance fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error fetching attendance: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class AttendanceDeleteView(APIView):
    def delete(self, request, id):
        try:
            user = request.user
            if not user.role or user.role.name != "admin":
                return Response({"msg": "Only admin can delete attendance records"}, status=status.HTTP_403_FORBIDDEN)
            record = Attendance.objects.filter(id=id).first()
            if not record:
                return Response({"msg": "Record not found"}, status=status.HTTP_404_NOT_FOUND)
            record.delete()
            return Response({"msg": "Attendance record deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error deleting attendance: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

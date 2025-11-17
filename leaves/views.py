from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from leaves.models import Leave
from leaves.serializers import LeaveSerializer
from accounts.models import User
from notifications.utils import notify_leave_status
import logging

logger = logging.getLogger(__name__)


def get_user_role(user):
    return user.role.name if user.role else None


class ApplyLeaveView(APIView):
    def post(self, request):
        try:
            serializer = LeaveSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response({"msg": "Leave applied successfully"}, status=status.HTTP_201_CREATED)
            return Response({"msg": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"msg": f"Error applying for leave: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class LeaveListView(APIView):
    def get(self, request):
        try:
            user = request.user
            role = get_user_role(user)
            if role == "admin":
                leaves = Leave.objects.all().order_by('-applied_on')
            elif role == "senior":
                dept_users = User.objects.filter(department=user.department)
                leaves = Leave.objects.filter(user__in=dept_users)
            elif role in ["junior", "intern"]:
                leaves = Leave.objects.filter(user=user)
            else:
                return Response({"msg": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)
            serializer = LeaveSerializer(leaves, many=True)
            return Response({"msg": "Leaves fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error fetching leaves: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class LeaveStatusUpdateView(APIView):
    def put(self, request, id):
        try:
            user = request.user
            role = get_user_role(user)
            leave = Leave.objects.filter(id=id).first()
            if not leave:
                return Response({"msg": "Leave not found"}, status=status.HTTP_404_NOT_FOUND)
            if role not in ["admin", "senior"]:
                return Response({"msg": "You do not have permission to update leave status"}, status=status.HTTP_403_FORBIDDEN)
            new_status = request.data.get("status")
            if new_status not in ["Approved", "Rejected"]:
                return Response({"msg": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
            leave.status = new_status
            leave.save()
            
            try:
                notify_leave_status(leave.user, new_status, user)
                logger.info(f"Leave status notification sent to {leave.user.username} - Status: {new_status}")
            except Exception as notif_error:
                logger.exception(f"Failed to send leave status notification: {notif_error}")
            
            return Response({"msg": f"Leave {new_status.lower()} successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error updating leave: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class LeaveDeleteView(APIView):
    def delete(self, request, id):
        try:
            user = request.user
            if not user.role or user.role.name != "admin":
                return Response({"msg": "Only admin can delete leave records"}, status=status.HTTP_403_FORBIDDEN)
            leave = Leave.objects.filter(id=id).first()
            if not leave:
                return Response({"msg": "Leave not found"}, status=status.HTTP_404_NOT_FOUND)
            leave.delete()
            return Response({"msg": "Leave deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error deleting leave: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

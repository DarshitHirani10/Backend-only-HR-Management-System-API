from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from accounts.models import User
from notifications.models import Notification


class NotificationListView(APIView):
    def get(self, request):
        try:
            user = request.user
            role = user.role.name if user.role else None
            if role == "admin":
                notifications = Notification.objects.all().order_by('-created_at')
            else:
                notifications = Notification.objects.filter(user=user).order_by('-created_at')
            serializer = NotificationSerializer(notifications, many=True)
            return Response({"msg": "Notifications fetched successfully", "data": serializer.data})
        except Exception as e:
            return Response({"msg": f"Error fetching notifications: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class MarkNotificationReadView(APIView):
    def patch(self, request, id):
        try:
            notification = Notification.objects.filter(id=id, user=request.user).first()
            if not notification:
                return Response({"msg": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
            notification.is_read = True
            notification.save()
            return Response({"msg": "Notification marked as read"})
        except Exception as e:
            return Response({"msg": f"Error marking as read: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class DeleteNotificationView(APIView):
    def delete(self, request, id):
        try:
            user = request.user
            role = user.role.name if user.role else None
            notification = Notification.objects.filter(id=id).first()
            if not notification:
                return Response({"msg": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
            if role != "admin" and notification.user != user:
                return Response({"msg": "You cannot delete this notification"}, status=status.HTTP_403_FORBIDDEN)
            notification.delete()
            return Response({"msg": "Notification deleted successfully"})
        except Exception as e:
            return Response({"msg": f"Error deleting notification: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

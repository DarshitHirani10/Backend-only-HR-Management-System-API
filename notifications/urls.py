from django.urls import path
from notifications.views import NotificationListView, MarkNotificationReadView, DeleteNotificationView

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='list-notifications'),
    path('notifications/read/<int:id>/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/delete/<int:id>/', DeleteNotificationView.as_view(), name='delete-notification'),
]

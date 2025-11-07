from django.urls import path
from attendance.views import CheckInView, CheckOutView, AttendanceListView, AttendanceDeleteView

urlpatterns = [
    path("attendance/checkin/", CheckInView.as_view(), name="checkin"),
    path("attendance/checkout/", CheckOutView.as_view(), name="checkout"),
    path("attendance/", AttendanceListView.as_view(), name="attendance-list"),
    path("attendance/delete/<int:id>/", AttendanceDeleteView.as_view(), name="attendance-delete"),
]

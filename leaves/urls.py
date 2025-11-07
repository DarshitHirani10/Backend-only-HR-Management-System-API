from django.urls import path
from leaves.views import ApplyLeaveView, LeaveListView, LeaveStatusUpdateView, LeaveDeleteView

urlpatterns = [
    path("leaves/apply/", ApplyLeaveView.as_view(), name="apply-leave"),
    path("leaves/", LeaveListView.as_view(), name="list-leaves"),
    path("leaves/update/<int:id>/", LeaveStatusUpdateView.as_view(), name="update-leave-status"),
    path("leaves/delete/<int:id>/", LeaveDeleteView.as_view(), name="delete-leave"),
]

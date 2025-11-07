from django.urls import path
from tasks.views import TaskListCreateView, TaskDetailView, TaskStatusUpdateView

urlpatterns = [
    path("tasks/", TaskListCreateView.as_view(), name="list-tasks"),
    path("tasks/create/", TaskListCreateView.as_view(), name="create-task"),
    path("tasks/<int:id>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/update/<int:id>/", TaskDetailView.as_view(), name="update-task"),
    path("tasks/delete/<int:id>/", TaskDetailView.as_view(), name="delete-task"),
    path("tasks/status/<int:id>/", TaskStatusUpdateView.as_view(), name="update-task-status"),
]

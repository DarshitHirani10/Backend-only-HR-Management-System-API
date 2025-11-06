from django.urls import path
from departments.views import DepartmentView, DesignationView

urlpatterns = [
    path("departments/", DepartmentView.as_view(), name="list-departments"),
    path("departments/create/", DepartmentView.as_view(), name="create-department"),
    path("departments/update/<int:id>/", DepartmentView.as_view(), name="update-department"),
    path("departments/delete/<int:id>/", DepartmentView.as_view(), name="delete-department"),

    path("designations/", DesignationView.as_view(), name="list-designations"),
    path("designations/create/", DesignationView.as_view(), name="create-designation"),
    path("designations/update/<int:id>/", DesignationView.as_view(), name="update-designation"),
    path("designations/delete/<int:id>/", DesignationView.as_view(), name="delete-designation"),
]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from tasks.models import Task
from tasks.serializers import TaskSerializer
from accounts.models import User

def get_user_role(user):
    return user.role.name if user.role else None


class TaskListCreateView(APIView):

    def get(self, request):
        try:
            role = get_user_role(request.user)
            if role == "admin":
                tasks = Task.objects.all()
            elif role == "senior":
                tasks = Task.objects.filter(created_by=request.user)
            elif role in ["junior", "intern"]:
                tasks = Task.objects.filter(assigned_to=request.user)
            else:
                return Response({"msg": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)
            serializer = TaskSerializer(tasks, many=True)
            return Response({"msg": "Tasks fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error fetching tasks: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            role = get_user_role(request.user)
            if role not in ["admin", "senior"]:
                return Response({"msg": "You do not have permission to create tasks"}, status=status.HTTP_403_FORBIDDEN)
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_by=request.user)
                return Response({"msg": "Task created successfully"}, status=status.HTTP_201_CREATED)
            return Response({"msg": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"msg": f"Error creating task: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class TaskDetailView(APIView):

    def get(self, request, id):
        try:
            task = Task.objects.filter(id=id).first()
            if not task:
                return Response({"msg": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = TaskSerializer(task)
            return Response({"msg": "Task details fetched", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error fetching task: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        try:
            task = Task.objects.filter(id=id).first()
            if not task:
                return Response({"msg": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
            role = get_user_role(request.user)
            if role not in ["admin", "senior"]:
                return Response({"msg": "You cannot edit this task"}, status=status.HTTP_403_FORBIDDEN)
            if role == "senior" and task.created_by != request.user:
                return Response({"msg": "You can only edit tasks you created"}, status=status.HTTP_403_FORBIDDEN)
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"msg": "Task updated successfully"}, status=status.HTTP_200_OK)
            return Response({"msg": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"msg": f"Error updating task: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            task = Task.objects.filter(id=id).first()
            if not task:
                return Response({"msg": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
            role = get_user_role(request.user)
            if role == "admin":
                pass
            elif role == "senior":
                if task.created_by != request.user:
                    return Response({"msg": "You can only delete tasks you created"}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({"msg": "You do not have permission to delete tasks"}, status=status.HTTP_403_FORBIDDEN)
            task.delete()
            return Response({"msg": "Task deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error deleting task: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class TaskStatusUpdateView(APIView):

    def patch(self, request, id):
        try:
            task = Task.objects.filter(id=id).first()
            if not task:
                return Response({"msg": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
            role = get_user_role(request.user)
            new_status = request.data.get("status")
            if not new_status:
                return Response({"msg": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)
            allowed_status = ["Pending", "In Progress", "Completed", "Reviewed"]
            if new_status not in allowed_status:
                return Response({"msg": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)
            if role == "admin":
                pass
            elif role == "senior":
                if task.created_by != request.user:
                    return Response({"msg": "You can only update status of your created tasks"}, status=status.HTTP_403_FORBIDDEN)
            elif role in ["junior", "intern"]:
                if task.assigned_to != request.user:
                    return Response({"msg": "You can only update status of your assigned tasks"}, status=status.HTTP_403_FORBIDDEN)
                if new_status not in ["In Progress", "Completed"]:
                    return Response({"msg": "You cannot set this status"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"msg": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)
            task.status = new_status
            task.save()
            return Response({"msg": f"Task status updated to '{new_status}'"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"msg": f"Error updating status: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

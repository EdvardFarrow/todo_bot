from rest_framework import viewsets, permissions
from apps.tasks.models import Task, Category
from apps.tasks.serializers import TaskSerializer, CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view or edit their categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only categories belonging to the current user."""
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Associate the new category with the current user."""
        serializer.save(user=self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view or edit their tasks.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only tasks belonging to the current user."""
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Associate the new task with the current user."""
        serializer.save(user=self.request.user)
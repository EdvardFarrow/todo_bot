from rest_framework import serializers
from apps.tasks.models import Task, Category

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Task Categories.
    """
    class Meta:
        model = Category
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]

class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Tasks.
    Includes category details for read operations.
    """
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source="category", 
        write_only=True, 
        required=False, 
        allow_null=True
    )
    # Read-only field to show category name in response
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", 
            "title", 
            "description", 
            "deadline", 
            "is_completed", 
            "category_id", 
            "category_name",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_category_id(self, value):
        """
        Ensure the category belongs to the current user.
        """
        user = self.context["request"].user
        if value and value.user != user:
            raise serializers.ValidationError("You cannot use a category that does not belong to you.")
        return value
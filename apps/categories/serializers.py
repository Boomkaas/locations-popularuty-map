from django.utils.text import slugify
from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "created_at"]
        read_only_fields = ["slug", "created_at"]

    def validate_name(self, value):
        slug = slugify(value, allow_unicode=True)
        if not slug:
            raise serializers.ValidationError("Name must contain letters or numbers.")

        categories = Category.objects.filter(slug=slug)
        if self.instance is not None:
            categories = categories.exclude(pk=self.instance.pk)
        if categories.exists():
            raise serializers.ValidationError("A category with a similar name already exists.")

        return value

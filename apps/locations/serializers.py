from rest_framework import serializers

from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")
    category_name = serializers.ReadOnlyField(source="category.name")
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-90, max_value=90)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-180, max_value=180)

    class Meta:
        model = Location
        fields = [
            "id",
            "title",
            "description",
            "category",
            "category_name",
            "address",
            "latitude",
            "longitude",
            "author",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class LocationListSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")
    category_name = serializers.ReadOnlyField(source="category.name")

    class Meta:
        model = Location
        fields = [
            "id",
            "title",
            "category",
            "category_name",
            "address",
            "latitude",
            "longitude",
            "author",
            "created_at",
        ]

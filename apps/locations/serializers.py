from rest_framework import serializers

from .models import Location


class RoundedFloatField(serializers.FloatField):
    def to_representation(self, value):
        return round(value, 2)


class LocationSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")
    category_name = serializers.ReadOnlyField(source="category.name")
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-90, max_value=90)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=-180, max_value=180)
    rating = RoundedFloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    views_last_7d = serializers.IntegerField(read_only=True)
    popularity = RoundedFloatField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

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
            "rating",
            "reviews_count",
            "views_last_7d",
            "popularity",
            "is_subscribed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_is_subscribed(self, location) -> bool:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return location.subscriptions.filter(user=request.user).exists()


class LocationListSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")
    category_name = serializers.ReadOnlyField(source="category.name")
    rating = RoundedFloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    views_last_7d = serializers.IntegerField(read_only=True)
    popularity = RoundedFloatField(read_only=True)

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
            "rating",
            "reviews_count",
            "views_last_7d",
            "popularity",
            "created_at",
        ]


class LocationMapSerializer(serializers.ModelSerializer):
    rating = RoundedFloatField(read_only=True)
    popularity = RoundedFloatField(read_only=True)

    class Meta:
        model = Location
        fields = ["id", "title", "latitude", "longitude", "rating", "popularity"]

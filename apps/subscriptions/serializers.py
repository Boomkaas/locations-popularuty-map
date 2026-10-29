from rest_framework import serializers

from .models import LocationSubscription


class SubscriptionSerializer(serializers.ModelSerializer):
    location_title = serializers.ReadOnlyField(source="location.title")

    class Meta:
        model = LocationSubscription
        fields = ["id", "location", "location_title", "created_at"]

from django.conf import settings
from django.db import models


class LocationSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location_subscriptions",
    )
    location = models.ForeignKey("locations.Location", on_delete=models.CASCADE, related_name="subscriptions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "location"], name="unique_subscription_per_user"),
        ]

    def __str__(self):
        return f"{self.user} - {self.location}"

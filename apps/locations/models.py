from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Cast, Coalesce, Ln
from django.utils import timezone

from apps.categories.models import Category
from apps.reviews.models import Review

from .cache import invalidate_locations_list


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class LocationQuerySet(SoftDeleteQuerySet):
    def delete(self):
        deleted_count = super().delete()
        transaction.on_commit(invalidate_locations_list)
        return deleted_count

    def with_stats(self):
        week_ago = timezone.now() - timedelta(days=7)
        reviews = Review.objects.filter(location=OuterRef("pk")).values("location")
        views = LocationView.objects.filter(location=OuterRef("pk"), viewed_at__gte=week_ago).values("location")

        locations = self.annotate(
            rating=Coalesce(
                Subquery(reviews.annotate(value=Avg("rating")).values("value"), output_field=FloatField()),
                Value(0.0),
            ),
            reviews_count=Coalesce(
                Subquery(reviews.annotate(value=Count("id")).values("value")),
                Value(0),
            ),
            views_last_7d=Coalesce(
                Subquery(views.annotate(value=Count("id")).values("value")),
                Value(0),
            ),
        )

        weights = settings.POPULARITY_WEIGHTS
        return locations.annotate(
            popularity=ExpressionWrapper(
                Value(weights["rating"]) * F("rating")
                + Value(weights["reviews"]) * Ln(Cast("reviews_count", FloatField()) + Value(1.0))
                + Value(weights["views"]) * Ln(Cast("views_last_7d", FloatField()) + Value(1.0)),
                output_field=FloatField(),
            )
        )


class LocationManager(models.Manager.from_queryset(LocationQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Location(SoftDeleteModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="locations")
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="locations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LocationManager()
    all_objects = LocationQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(latitude__gte=-90, latitude__lte=90),
                name="location_latitude_range",
            ),
            models.CheckConstraint(
                condition=Q(longitude__gte=-180, longitude__lte=180),
                name="location_longitude_range",
            ),
        ]

    def __str__(self):
        return self.title


class LocationView(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_views",
    )
    viewer_key = models.CharField(max_length=100)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["location", "viewed_at"]),
        ]

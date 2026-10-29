from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, OuterRef, Q, Subquery


class ReviewQuerySet(models.QuerySet):
    def with_reactions(self, user):
        my_reaction = ReviewReaction.objects.filter(review=OuterRef("pk"), user_id=user.pk).values("value")
        return self.annotate(
            likes_count=Count("reactions", filter=Q(reactions__value=ReviewReaction.Value.LIKE)),
            dislikes_count=Count("reactions", filter=Q(reactions__value=ReviewReaction.Value.DISLIKE)),
            my_reaction=Subquery(my_reaction),
        )


class Review(models.Model):
    location = models.ForeignKey("locations.Location", on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["location", "author"], name="unique_review_per_user"),
            models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name="review_rating_1_5"),
        ]

    def __str__(self):
        return f"{self.author} - {self.location} ({self.rating})"


class ReviewReaction(models.Model):
    class Value(models.IntegerChoices):
        LIKE = 1, "Like"
        DISLIKE = -1, "Dislike"

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_reactions",
    )
    value = models.SmallIntegerField(choices=Value.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "user"], name="unique_reaction_per_user"),
        ]

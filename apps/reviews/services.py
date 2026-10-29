from django.db import IntegrityError, transaction

from apps.subscriptions.tasks import notify_new_review

from .exceptions import ConflictError
from .models import Review, ReviewReaction

REVIEW_EXISTS_ERROR = {
    "detail": "You have already reviewed this location.",
    "code": "review_already_exists",
}
REACTION_EXISTS_ERROR = {
    "detail": "You have already reacted to this review.",
    "code": "reaction_already_exists",
}


def create_review(location, author, rating, text):
    if Review.objects.filter(location=location, author=author).exists():
        raise ConflictError(REVIEW_EXISTS_ERROR)

    try:
        with transaction.atomic():
            review = Review.objects.create(location=location, author=author, rating=rating, text=text)
    except IntegrityError:
        raise ConflictError(REVIEW_EXISTS_ERROR)

    transaction.on_commit(lambda: notify_new_review.delay(review.id))
    return review


def add_reaction(review, user, value):
    if ReviewReaction.objects.filter(review=review, user=user).exists():
        raise ConflictError(REACTION_EXISTS_ERROR)

    try:
        with transaction.atomic():
            return ReviewReaction.objects.create(review=review, user=user, value=value)
    except IntegrityError:
        raise ConflictError(REACTION_EXISTS_ERROR)


def remove_reaction(review, user):
    deleted_count, _ = ReviewReaction.objects.filter(review=review, user=user).delete()
    return deleted_count > 0

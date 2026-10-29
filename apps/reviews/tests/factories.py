import factory

from apps.locations.tests.factories import LocationFactory
from apps.reviews.models import Review
from apps.users.tests.factories import UserFactory


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    location = factory.SubFactory(LocationFactory)
    author = factory.SubFactory(UserFactory)
    rating = 4
    text = "Good place"

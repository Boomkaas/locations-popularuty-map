from decimal import Decimal

import factory

from apps.categories.tests.factories import CategoryFactory
from apps.locations.models import Location
from apps.users.tests.factories import UserFactory


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    title = factory.Sequence(lambda number: f"Location {number}")
    description = "Nice place"
    category = factory.SubFactory(CategoryFactory)
    address = "Kyiv"
    latitude = Decimal("50.450000")
    longitude = Decimal("30.520000")
    author = factory.SubFactory(UserFactory)

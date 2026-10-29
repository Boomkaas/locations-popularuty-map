import math

import pytest

from apps.reviews.tests.factories import ReviewFactory

from .factories import LocationFactory

pytestmark = pytest.mark.django_db

LOCATIONS_URL = "/api/v1/locations/"


def test_rating_is_average_of_reviews(api_client):
    location = LocationFactory()
    ReviewFactory(location=location, rating=3)
    ReviewFactory(location=location, rating=5)

    result = api_client.get(LOCATIONS_URL).data["results"][0]

    assert result["rating"] == 4.0
    assert result["reviews_count"] == 2


def test_popularity_uses_formula(api_client):
    location = LocationFactory()
    ReviewFactory(location=location, rating=3)
    ReviewFactory(location=location, rating=5)

    result = api_client.get(LOCATIONS_URL).data["results"][0]

    expected = 2.0 * 4 + 1.5 * math.log(1 + 2) + 1.0 * math.log(1 + 0)
    assert result["popularity"] == round(expected, 2)


def test_location_without_reviews_has_zero_rating(api_client):
    LocationFactory()

    result = api_client.get(LOCATIONS_URL).data["results"][0]

    assert result["rating"] == 0
    assert result["popularity"] == 0


def test_ordering_by_popularity(api_client):
    popular = LocationFactory(title="Popular")
    quiet = LocationFactory(title="Quiet")
    ReviewFactory(location=popular, rating=5)
    ReviewFactory(location=popular, rating=5)
    ReviewFactory(location=quiet, rating=2)

    results = api_client.get(LOCATIONS_URL, {"ordering": "-popularity"}).data["results"]

    assert [item["title"] for item in results] == ["Popular", "Quiet"]

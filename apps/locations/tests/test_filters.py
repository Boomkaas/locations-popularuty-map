import pytest

from apps.categories.tests.factories import CategoryFactory
from apps.reviews.tests.factories import ReviewFactory
from apps.users.tests.factories import UserFactory

from .factories import LocationFactory

pytestmark = pytest.mark.django_db

LOCATIONS_URL = "/api/v1/locations/"


def get_titles(client, params):
    response = client.get(LOCATIONS_URL, params)
    return [item["title"] for item in response.data["results"]]


def test_search_by_title_and_description(api_client):
    LocationFactory(title="Shevchenko Park")
    LocationFactory(title="Market", description="Near a park")
    LocationFactory(title="Museum")

    titles = get_titles(api_client, {"search": "park"})

    assert sorted(titles) == ["Market", "Shevchenko Park"]


def test_filter_by_category(api_client):
    parks = CategoryFactory(name="Parks")
    LocationFactory(title="Park", category=parks)
    LocationFactory(title="Museum")

    assert get_titles(api_client, {"category": parks.pk}) == ["Park"]
    assert get_titles(api_client, {"category_slug": "parks"}) == ["Park"]


def test_filter_by_author(api_client):
    olena = UserFactory(username="olena")
    LocationFactory(title="Olena place", author=olena)
    LocationFactory(title="Other place")

    assert get_titles(api_client, {"author": olena.pk}) == ["Olena place"]
    assert get_titles(api_client, {"author_username": "OLENA"}) == ["Olena place"]


def test_filter_by_rating(api_client):
    good = LocationFactory(title="Good")
    bad = LocationFactory(title="Bad")
    ReviewFactory(location=good, rating=5)
    ReviewFactory(location=bad, rating=2)

    assert get_titles(api_client, {"min_rating": 4}) == ["Good"]
    assert get_titles(api_client, {"max_rating": 3}) == ["Bad"]


def test_ordering_by_rating(api_client):
    good = LocationFactory(title="Good")
    bad = LocationFactory(title="Bad")
    ReviewFactory(location=good, rating=5)
    ReviewFactory(location=bad, rating=2)

    assert get_titles(api_client, {"ordering": "rating"}) == ["Bad", "Good"]
    assert get_titles(api_client, {"ordering": "-rating"}) == ["Good", "Bad"]


def test_page_size(api_client):
    LocationFactory.create_batch(3)

    response = api_client.get(LOCATIONS_URL, {"page_size": 2})

    assert response.data["count"] == 3
    assert len(response.data["results"]) == 2
    assert response.data["next"] is not None

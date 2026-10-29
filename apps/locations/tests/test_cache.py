import pytest

from apps.reviews.tests.factories import ReviewFactory

from .factories import LocationFactory

pytestmark = pytest.mark.django_db

LOCATIONS_URL = "/api/v1/locations/"


def test_second_request_is_served_from_cache(api_client, django_assert_num_queries):
    LocationFactory()
    api_client.get(LOCATIONS_URL)

    with django_assert_num_queries(0):
        response = api_client.get(LOCATIONS_URL)

    assert response.status_code == 200
    assert response.data["count"] == 1


def test_new_review_refreshes_cached_list(api_client, django_capture_on_commit_callbacks):
    location = LocationFactory()
    first_response = api_client.get(LOCATIONS_URL)
    assert first_response.data["results"][0]["rating"] == 0

    with django_capture_on_commit_callbacks(execute=True):
        ReviewFactory(location=location, rating=5)

    second_response = api_client.get(LOCATIONS_URL)
    assert second_response.data["results"][0]["rating"] == 5.0

import pytest

from apps.categories.tests.factories import CategoryFactory
from apps.locations.models import Location

from .factories import LocationFactory

pytestmark = pytest.mark.django_db

LOCATIONS_URL = "/api/v1/locations/"


def location_url(location_id):
    return f"{LOCATIONS_URL}{location_id}/"


def location_data(category):
    return {
        "title": "Shevchenko Park",
        "description": "Central park",
        "category": category.pk,
        "address": "Kyiv",
        "latitude": "50.441900",
        "longitude": "30.513300",
    }


def test_anonymous_cannot_create_location(api_client):
    response = api_client.post(LOCATIONS_URL, location_data(CategoryFactory()), format="json")

    assert response.status_code == 403


def test_user_creates_location_as_author(user_client, user):
    response = user_client.post(LOCATIONS_URL, location_data(CategoryFactory()), format="json")

    assert response.status_code == 201
    assert response.data["author"] == user.username


def test_latitude_out_of_range_returns_400(user_client):
    data = location_data(CategoryFactory())
    data["latitude"] = "91"
    response = user_client.post(LOCATIONS_URL, data, format="json")

    assert response.status_code == 400
    assert "latitude" in response.data


def test_user_cannot_update_other_users_location(user_client):
    location = LocationFactory()
    response = user_client.patch(location_url(location.pk), {"title": "Changed"}, format="json")

    assert response.status_code == 403


def test_admin_can_update_any_location(staff_client):
    location = LocationFactory()
    response = staff_client.patch(location_url(location.pk), {"title": "Changed"}, format="json")

    assert response.status_code == 200
    assert response.data["title"] == "Changed"


def test_delete_is_soft(user_client, user):
    location = LocationFactory(author=user)

    response = user_client.delete(location_url(location.pk))

    assert response.status_code == 204
    assert Location.all_objects.get(pk=location.pk).is_deleted is True
    assert user_client.get(LOCATIONS_URL).data["count"] == 0
    assert user_client.get(location_url(location.pk)).status_code == 404

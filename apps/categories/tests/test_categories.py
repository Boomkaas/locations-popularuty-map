import pytest

from apps.locations.tests.factories import LocationFactory

from .factories import CategoryFactory

pytestmark = pytest.mark.django_db

CATEGORIES_URL = "/api/v1/categories/"


def category_url(category_id):
    return f"{CATEGORIES_URL}{category_id}/"


def test_anonymous_can_read_categories(api_client):
    CategoryFactory()
    response = api_client.get(CATEGORIES_URL)

    assert response.status_code == 200
    assert response.data["count"] == 1


def test_user_cannot_create_category(user_client):
    response = user_client.post(CATEGORIES_URL, {"name": "Parks"}, format="json")

    assert response.status_code == 403


def test_admin_can_create_update_and_delete_category(staff_client):
    create_response = staff_client.post(CATEGORIES_URL, {"name": "Parks"}, format="json")
    assert create_response.status_code == 201
    assert create_response.data["slug"] == "parks"

    category_id = create_response.data["id"]
    update_response = staff_client.patch(category_url(category_id), {"name": "City parks"}, format="json")
    assert update_response.status_code == 200
    assert update_response.data["slug"] == "city-parks"

    delete_response = staff_client.delete(category_url(category_id))
    assert delete_response.status_code == 204


def test_category_with_locations_cannot_be_deleted(staff_client):
    category = CategoryFactory()
    LocationFactory(category=category)

    response = staff_client.delete(category_url(category.pk))

    assert response.status_code == 409

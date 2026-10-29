import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.locations.models import LocationView
from apps.users.tests.factories import UserFactory

from .factories import LocationFactory

pytestmark = pytest.mark.django_db


def location_url(location_id):
    return f"/api/v1/locations/{location_id}/"


def logged_in_client():
    client = APIClient()
    client.force_login(UserFactory())
    return client


def test_same_user_is_counted_once_per_hour(user_client):
    location = LocationFactory()

    user_client.get(location_url(location.pk))
    user_client.get(location_url(location.pk))

    assert LocationView.objects.filter(location=location).count() == 1


def test_two_users_are_counted_twice():
    location = LocationFactory()

    logged_in_client().get(location_url(location.pk))
    logged_in_client().get(location_url(location.pk))

    assert LocationView.objects.filter(location=location).count() == 2


def test_user_is_counted_again_after_key_expires(user_client):
    location = LocationFactory()

    user_client.get(location_url(location.pk))
    cache.clear()
    user_client.get(location_url(location.pk))

    assert LocationView.objects.filter(location=location).count() == 2


def test_anonymous_visitor_is_counted_once(api_client):
    location = LocationFactory()

    api_client.get(location_url(location.pk), HTTP_USER_AGENT="firefox")
    api_client.get(location_url(location.pk), HTTP_USER_AGENT="firefox")

    assert LocationView.objects.filter(location=location).count() == 1


def test_deleted_location_is_not_counted(api_client):
    location = LocationFactory()
    location.delete()

    response = api_client.get(location_url(location.pk))

    assert response.status_code == 404
    assert LocationView.objects.count() == 0

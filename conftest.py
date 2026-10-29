import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_client(user):
    client = APIClient()
    client.force_login(user)
    return client


@pytest.fixture
def staff_user():
    return UserFactory(is_staff=True)


@pytest.fixture
def staff_client(staff_user):
    client = APIClient()
    client.force_login(staff_user)
    return client

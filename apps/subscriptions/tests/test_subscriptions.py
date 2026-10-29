import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.locations.tests.factories import LocationFactory
from apps.subscriptions.models import LocationSubscription
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

SUBSCRIPTIONS_URL = "/api/v1/subscriptions/"


def subscribe_url(location_id):
    return f"/api/v1/locations/{location_id}/subscribe/"


def location_reviews_url(location_id):
    return f"/api/v1/locations/{location_id}/reviews/"


def test_subscribe_returns_201_then_200(user_client, user):
    location = LocationFactory()

    first_response = user_client.post(subscribe_url(location.pk))
    second_response = user_client.post(subscribe_url(location.pk))

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert LocationSubscription.objects.filter(user=user, location=location).count() == 1


def test_unsubscribe_returns_204(user_client, user):
    location = LocationFactory()
    LocationSubscription.objects.create(user=user, location=location)

    response = user_client.delete(subscribe_url(location.pk))

    assert response.status_code == 204
    assert LocationSubscription.objects.count() == 0


def test_anonymous_cannot_subscribe(api_client):
    location = LocationFactory()

    response = api_client.post(subscribe_url(location.pk))

    assert response.status_code == 403


def test_my_subscriptions_list(user_client, user):
    my_location = LocationFactory(title="Mine")
    LocationSubscription.objects.create(user=user, location=my_location)
    LocationSubscription.objects.create(user=UserFactory(), location=LocationFactory())

    response = user_client.get(SUBSCRIPTIONS_URL)

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["location_title"] == "Mine"


def test_location_details_show_is_subscribed(user_client, user):
    location = LocationFactory()
    assert user_client.get(f"/api/v1/locations/{location.pk}/").data["is_subscribed"] is False

    LocationSubscription.objects.create(user=user, location=location)

    assert user_client.get(f"/api/v1/locations/{location.pk}/").data["is_subscribed"] is True


def test_new_review_notifies_author_and_subscribers(django_capture_on_commit_callbacks):
    author = UserFactory()
    subscriber = UserFactory()
    location = LocationFactory(author=author)
    LocationSubscription.objects.create(user=author, location=location)
    LocationSubscription.objects.create(user=subscriber, location=location)
    reviewer = UserFactory()
    client = APIClient()
    client.force_login(reviewer)

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(location_reviews_url(location.pk), {"rating": 5, "text": "Great"}, format="json")

    assert response.status_code == 201
    recipients = sorted(message.to[0] for message in mail.outbox)
    assert recipients == sorted([author.email, subscriber.email])
    assert location.title in mail.outbox[0].subject


def test_reviewer_does_not_get_own_notification(django_capture_on_commit_callbacks):
    location = LocationFactory()
    reviewer = UserFactory()
    LocationSubscription.objects.create(user=reviewer, location=location)
    client = APIClient()
    client.force_login(reviewer)

    with django_capture_on_commit_callbacks(execute=True):
        client.post(location_reviews_url(location.pk), {"rating": 5, "text": "Great"}, format="json")

    recipients = [message.to[0] for message in mail.outbox]
    assert recipients == [location.author.email]

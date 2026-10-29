import pytest
from rest_framework.test import APIClient

from apps.locations.tests.factories import LocationFactory
from apps.users.tests.factories import UserFactory

from .factories import ReviewFactory

pytestmark = pytest.mark.django_db


def location_reviews_url(location_id):
    return f"/api/v1/locations/{location_id}/reviews/"


def reaction_url(review_id):
    return f"/api/v1/reviews/{review_id}/reaction/"


def logged_in_client():
    client = APIClient()
    client.force_login(UserFactory())
    return client


def test_user_creates_review(user_client, user):
    location = LocationFactory()
    response = user_client.post(location_reviews_url(location.pk), {"rating": 5, "text": "Great"}, format="json")

    assert response.status_code == 201
    assert response.data["author"] == user.username


def test_second_review_returns_409(user_client, user):
    location = LocationFactory()
    ReviewFactory(location=location, author=user)

    response = user_client.post(location_reviews_url(location.pk), {"rating": 4, "text": "Again"}, format="json")

    assert response.status_code == 409
    assert response.data["code"] == "review_already_exists"


def test_rating_above_five_returns_400(user_client):
    location = LocationFactory()
    response = user_client.post(location_reviews_url(location.pk), {"rating": 6, "text": "Too much"}, format="json")

    assert response.status_code == 400


def test_anonymous_cannot_create_review(api_client):
    location = LocationFactory()
    response = api_client.post(location_reviews_url(location.pk), {"rating": 5, "text": "Great"}, format="json")

    assert response.status_code == 403


def test_reviews_of_deleted_location_return_404(api_client):
    location = LocationFactory()
    location.delete()

    response = api_client.get(location_reviews_url(location.pk))

    assert response.status_code == 404


def test_first_reaction_returns_201(user_client):
    review = ReviewFactory()
    response = user_client.post(reaction_url(review.pk), {"value": "like"}, format="json")

    assert response.status_code == 201
    assert response.data["likes_count"] == 1
    assert response.data["my_reaction"] == "like"


def test_second_reaction_returns_409(user_client):
    review = ReviewFactory()
    user_client.post(reaction_url(review.pk), {"value": "like"}, format="json")

    response = user_client.post(reaction_url(review.pk), {"value": "dislike"}, format="json")

    assert response.status_code == 409


def test_reaction_counters():
    review = ReviewFactory()
    logged_in_client().post(reaction_url(review.pk), {"value": "like"}, format="json")
    logged_in_client().post(reaction_url(review.pk), {"value": "like"}, format="json")
    logged_in_client().post(reaction_url(review.pk), {"value": "dislike"}, format="json")

    response = APIClient().get(f"/api/v1/reviews/{review.pk}/")

    assert response.data["likes_count"] == 2
    assert response.data["dislikes_count"] == 1


def test_reaction_can_be_withdrawn(user_client):
    review = ReviewFactory()
    user_client.post(reaction_url(review.pk), {"value": "like"}, format="json")

    delete_response = user_client.delete(reaction_url(review.pk))
    again_response = user_client.post(reaction_url(review.pk), {"value": "dislike"}, format="json")

    assert delete_response.status_code == 204
    assert again_response.status_code == 201

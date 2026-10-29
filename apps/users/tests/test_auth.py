import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from .factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

CSRF_URL = "/api/v1/auth/csrf/"
REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
ME_URL = "/api/v1/auth/me/"
RESET_URL = "/api/v1/auth/password-reset/"
RESET_CONFIRM_URL = "/api/v1/auth/password-reset/confirm/"


def test_register_creates_user_and_logs_in(api_client):
    data = {
        "username": "olena",
        "email": "olena@example.com",
        "password": DEFAULT_PASSWORD,
        "password2": DEFAULT_PASSWORD,
    }
    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 201
    assert response.data["username"] == "olena"
    assert "sessionid" in response.cookies


def test_register_with_different_passwords_returns_400(api_client):
    data = {
        "username": "olena",
        "email": "olena@example.com",
        "password": DEFAULT_PASSWORD,
        "password2": "OtherPass123!",
    }
    response = api_client.post(REGISTER_URL, data, format="json")

    assert response.status_code == 400
    assert "password2" in response.data


def test_login_with_correct_password_sets_session(api_client):
    UserFactory(username="olena")
    response = api_client.post(LOGIN_URL, {"username": "olena", "password": DEFAULT_PASSWORD}, format="json")

    assert response.status_code == 200
    assert "sessionid" in response.cookies


def test_login_with_wrong_password_returns_400(api_client):
    UserFactory(username="olena")
    response = api_client.post(LOGIN_URL, {"username": "olena", "password": "wrong"}, format="json")

    assert response.status_code == 400


def test_me_after_logout_returns_403(api_client):
    UserFactory(username="olena")
    api_client.post(LOGIN_URL, {"username": "olena", "password": DEFAULT_PASSWORD}, format="json")
    assert api_client.get(ME_URL).status_code == 200

    response = api_client.post(LOGOUT_URL)

    assert response.status_code == 204
    assert api_client.get(ME_URL).status_code == 403


def test_login_without_csrf_token_returns_403():
    client = APIClient(enforce_csrf_checks=True)
    UserFactory(username="olena")
    response = client.post(LOGIN_URL, {"username": "olena", "password": DEFAULT_PASSWORD}, format="json")

    assert response.status_code == 403


def test_login_with_csrf_token_returns_200():
    client = APIClient(enforce_csrf_checks=True)
    UserFactory(username="olena")
    client.get(CSRF_URL)
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        LOGIN_URL,
        {"username": "olena", "password": DEFAULT_PASSWORD},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert response.status_code == 200


def test_password_reset_sends_email_to_existing_user(api_client):
    UserFactory(email="olena@example.com")
    response = api_client.post(RESET_URL, {"email": "olena@example.com"}, format="json")

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["olena@example.com"]


def test_password_reset_for_unknown_email_returns_200_without_email(api_client):
    response = api_client.post(RESET_URL, {"email": "nobody@example.com"}, format="json")

    assert response.status_code == 200
    assert len(mail.outbox) == 0


def test_password_reset_confirm_sets_new_password(api_client):
    user = UserFactory(username="olena")
    data = {
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": default_token_generator.make_token(user),
        "new_password": "NewStrongPass456!",
    }
    response = api_client.post(RESET_CONFIRM_URL, data, format="json")

    assert response.status_code == 200
    login_response = api_client.post(
        LOGIN_URL,
        {"username": "olena", "password": "NewStrongPass456!"},
        format="json",
    )
    assert login_response.status_code == 200


def test_password_reset_confirm_with_bad_token_returns_400(api_client):
    user = UserFactory()
    data = {
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": "bad-token",
        "new_password": "NewStrongPass456!",
    }
    response = api_client.post(RESET_CONFIRM_URL, data, format="json")

    assert response.status_code == 400

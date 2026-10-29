import factory

from apps.users.models import User

DEFAULT_PASSWORD = "StrongPass123!"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda number: f"user{number}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.com")
    password = factory.django.Password(DEFAULT_PASSWORD)

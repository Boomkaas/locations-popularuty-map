import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.categories.models import Category
from apps.locations.models import Location, LocationView
from apps.reviews.models import Review
from apps.users.models import User

DEMO_PASSWORD = "DemoPass123!"
USERNAMES = ["olena", "taras", "maria", "andrii", "iryna"]
CATEGORIES = {
    "Parks": "Parks, gardens and other green places",
    "Museums": "Museums and galleries",
    "Cafes": "Cafes and coffee shops",
    "Monuments": "Monuments and historical places",
    "Viewpoints": "Places with a nice view of the city",
}
CITIES = [
    ("Kyiv", Decimal("50.450100"), Decimal("30.523400")),
    ("Lviv", Decimal("49.839700"), Decimal("24.029700")),
    ("Odesa", Decimal("46.482500"), Decimal("30.723300")),
    ("Kharkiv", Decimal("49.993500"), Decimal("36.230400")),
    ("Dnipro", Decimal("48.464700"), Decimal("35.046200")),
    ("Vinnytsia", Decimal("49.233100"), Decimal("28.468200")),
]
LOCATIONS_COUNT = 30
REVIEW_TEXTS = [
    "Great place, I will come back.",
    "Nice, but too many people on weekends.",
    "Not bad, worth a short visit.",
    "One of my favourite places in the city.",
    "Expected more, but it was ok.",
]


class Command(BaseCommand):
    help = "Fill the database with demo users, categories, locations, reviews and views."

    def handle(self, *args, **options):
        randomizer = random.Random(42)
        users = self.create_users()
        categories = self.create_categories()

        new_locations = 0
        for number in range(1, LOCATIONS_COUNT + 1):
            location, created = self.create_location(number, users, categories, randomizer)
            if created:
                self.create_reviews(location, users, randomizer)
                self.create_views(location, randomizer)
                new_locations += 1

        self.stdout.write(f"Demo data is ready. New locations: {new_locations}.")
        self.stdout.write(f"Demo users: {', '.join(USERNAMES)}. Password: {DEMO_PASSWORD}")

    def create_users(self):
        users = []
        for username in USERNAMES:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users.append(user)
        return users

    def create_categories(self):
        categories = []
        for name, description in CATEGORIES.items():
            category, _ = Category.objects.get_or_create(name=name, defaults={"description": description})
            categories.append(category)
        return categories

    def create_location(self, number, users, categories, randomizer):
        city_name, city_latitude, city_longitude = CITIES[number % len(CITIES)]
        category = categories[number % len(categories)]
        latitude = city_latitude + Decimal(randomizer.randint(-500, 500)) / 10000
        longitude = city_longitude + Decimal(randomizer.randint(-500, 500)) / 10000

        return Location.objects.get_or_create(
            title=f"{category.name[:-1]} in {city_name} #{number}",
            defaults={
                "description": f"{category.description} in {city_name}.",
                "category": category,
                "address": f"{city_name}, street {number}",
                "latitude": latitude,
                "longitude": longitude,
                "author": randomizer.choice(users),
            },
        )

    def create_reviews(self, location, users, randomizer):
        reviewers = [user for user in users if user != location.author]
        reviews_count = randomizer.randint(0, len(reviewers))
        for reviewer in randomizer.sample(reviewers, reviews_count):
            Review.objects.create(
                location=location,
                author=reviewer,
                rating=randomizer.randint(1, 5),
                text=randomizer.choice(REVIEW_TEXTS),
            )

    def create_views(self, location, randomizer):
        for number in range(randomizer.randint(0, 40)):
            view = LocationView.objects.create(location=location, viewer_key=f"seed:{location.pk}:{number}")
            viewed_at = timezone.now() - timedelta(hours=randomizer.randint(0, 24 * 10))
            LocationView.objects.filter(pk=view.pk).update(viewed_at=viewed_at)

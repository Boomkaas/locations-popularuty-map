from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.locations.models import LocationView


class Command(BaseCommand):
    help = "Delete location views older than the given number of days."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        border_date = timezone.now() - timedelta(days=options["days"])
        deleted_count, _ = LocationView.objects.filter(viewed_at__lt=border_date).delete()
        self.stdout.write(f"Deleted {deleted_count} old views.")

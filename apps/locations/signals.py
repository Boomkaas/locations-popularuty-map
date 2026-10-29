from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.categories.models import Category
from apps.reviews.models import Review

from .cache import invalidate_locations_list
from .models import Location


@receiver(post_save, sender=Location)
@receiver(post_delete, sender=Location)
@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
@receiver(post_save, sender=Category)
def clear_locations_list_cache(sender, **kwargs):
    transaction.on_commit(invalidate_locations_list)

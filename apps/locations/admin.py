from django.contrib import admin

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "author", "is_deleted", "created_at"]
    list_filter = ["is_deleted", "category"]
    search_fields = ["title", "address"]
    actions = ["restore_locations"]

    def get_queryset(self, request):
        return Location.all_objects.select_related("category", "author")

    @admin.action(description="Restore selected locations")
    def restore_locations(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)

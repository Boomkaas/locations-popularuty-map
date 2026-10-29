from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .cache import LIST_TTL, list_cache_key
from .export import EXPORT_CONTENT_TYPES, export_locations
from .filters import LocationFilter, StableOrderingFilter
from .models import Location
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import LocationListSerializer, LocationMapSerializer, LocationSerializer
from .services import register_view

POPULAR_LIMIT = 10


class LocationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, StableOrderingFilter]
    filterset_class = LocationFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "rating", "popularity", "reviews_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Location.objects.select_related("category", "author").with_stats()

    def get_serializer_class(self):
        if self.action in ["list", "popular"]:
            return LocationListSerializer
        if self.action == "map":
            return LocationMapSerializer
        return LocationSerializer

    def list(self, request, *args, **kwargs):
        cache_key = list_cache_key(request)
        data = cache.get(cache_key)
        if data is None:
            data = super().list(request, *args, **kwargs).data
            cache.set(cache_key, data, LIST_TTL)
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        location = self.get_object()
        register_view(location, request)
        serializer = self.get_serializer(location)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(responses=LocationMapSerializer(many=True))
    @action(detail=False, methods=["get"])
    def map(self, request):
        locations = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[OpenApiParameter("export_format", enum=["csv", "json"], default="csv")],
        responses={200: OpenApiTypes.BINARY},
        filters=True,
    )
    @action(detail=False, methods=["get"])
    def export(self, request):
        export_format = request.query_params.get("export_format", "csv")
        if export_format not in EXPORT_CONTENT_TYPES:
            raise ValidationError({"export_format": "Allowed values: csv, json."})

        locations = self.filter_queryset(self.get_queryset())
        body = export_locations(locations, export_format)

        file_date = timezone.now().strftime("%Y%m%d_%H%M")
        response = HttpResponse(body, content_type=EXPORT_CONTENT_TYPES[export_format])
        response["Content-Disposition"] = f'attachment; filename="locations_{file_date}.{export_format}"'
        return response

    @extend_schema(responses=LocationListSerializer(many=True))
    @action(detail=False, methods=["get"])
    def popular(self, request):
        locations = self.get_queryset().order_by("-popularity", "-id")[:POPULAR_LIMIT]
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

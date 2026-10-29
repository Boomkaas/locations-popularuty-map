from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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

    @extend_schema(responses=LocationListSerializer(many=True))
    @action(detail=False, methods=["get"])
    def popular(self, request):
        locations = self.get_queryset().order_by("-popularity", "-id")[:POPULAR_LIMIT]
        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

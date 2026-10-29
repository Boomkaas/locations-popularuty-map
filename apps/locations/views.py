from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from .models import Location
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import LocationListSerializer, LocationSerializer


class LocationViewSet(ModelViewSet):
    queryset = Location.objects.select_related("category", "author")
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return LocationListSerializer
        return LocationSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

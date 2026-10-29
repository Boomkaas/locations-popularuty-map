from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.locations.models import Location

from .models import LocationSubscription
from .serializers import SubscriptionSerializer
from .services import subscribe, unsubscribe


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={201: SubscriptionSerializer, 200: SubscriptionSerializer})
    def post(self, request, location_id):
        location = get_object_or_404(Location.objects, pk=location_id)
        subscription, created = subscribe(request.user, location)

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(SubscriptionSerializer(subscription).data, status=response_status)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, location_id):
        location = get_object_or_404(Location.objects, pk=location_id)
        unsubscribe(request.user, location)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListView(ListAPIView):
    queryset = LocationSubscription.objects.none()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        subscriptions = LocationSubscription.objects.filter(user=self.request.user, location__is_deleted=False)
        return subscriptions.select_related("location")

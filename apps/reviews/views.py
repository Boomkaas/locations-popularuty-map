from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListCreateAPIView
from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.locations.models import Location
from apps.locations.permissions import IsAuthorOrAdminOrReadOnly

from .models import Review
from .serializers import REACTION_VALUES, ReactionSerializer, ReviewSerializer
from .services import add_reaction, create_review, remove_reaction


class LocationReviewListView(ListCreateAPIView):
    serializer_class = ReviewSerializer
    ordering_fields = ["created_at", "rating", "likes_count"]
    ordering = ["-created_at"]

    def get_location(self):
        return get_object_or_404(Location.objects, pk=self.kwargs["location_id"])

    def get_queryset(self):
        location = self.get_location()
        reviews = Review.objects.filter(location=location).select_related("author")
        return reviews.with_reactions(self.request.user)

    def create(self, request, *args, **kwargs):
        location = self.get_location()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = create_review(location=location, author=request.user, **serializer.validated_data)

        review = self.get_queryset().get(pk=review.pk)
        return Response(self.get_serializer(review).data, status=status.HTTP_201_CREATED)


class ReviewViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    def get_queryset(self):
        reviews = Review.objects.filter(location__is_deleted=False).select_related("author")
        return reviews.with_reactions(self.request.user)

    def get_serializer_class(self):
        if self.action == "reaction":
            return ReactionSerializer
        return ReviewSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reaction(self, request, pk=None):
        review = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_reaction(review, request.user, REACTION_VALUES[serializer.validated_data["value"]])

        review = self.get_object()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)

    @reaction.mapping.delete
    def delete_reaction(self, request, pk=None):
        review = self.get_object()
        if not remove_reaction(review, request.user):
            return Response(
                {"detail": "You have not reacted to this review."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

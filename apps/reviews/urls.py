from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LocationReviewListView, ReviewViewSet

router = DefaultRouter()
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path(
        "locations/<int:location_id>/reviews/",
        LocationReviewListView.as_view(),
        name="location-reviews",
    ),
]
urlpatterns += router.urls

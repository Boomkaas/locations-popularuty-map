from django.urls import path

from .views import SubscribeView, SubscriptionListView

urlpatterns = [
    path("locations/<int:location_id>/subscribe/", SubscribeView.as_view(), name="location-subscribe"),
    path("subscriptions/", SubscriptionListView.as_view(), name="subscriptions"),
]

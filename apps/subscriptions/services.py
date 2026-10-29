from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.urls import reverse

from apps.reviews.models import Review

from .models import LocationSubscription


def subscribe(user, location):
    return LocationSubscription.objects.get_or_create(user=user, location=location)


def unsubscribe(user, location):
    LocationSubscription.objects.filter(user=user, location=location).delete()


def get_review_recipients(review):
    location = review.location
    recipients = {location.author}
    for subscription in location.subscriptions.select_related("user"):
        recipients.add(subscription.user)

    recipients.discard(review.author)
    return [user for user in recipients if user.email]


def send_new_review_emails(review_id):
    review = Review.objects.select_related("location__author", "author").filter(pk=review_id).first()
    if review is None:
        return 0

    location = review.location
    context = {
        "review": review,
        "location": location,
        "location_url": reverse("location-detail", args=[location.pk]),
        "unsubscribe_url": reverse("location-subscribe", args=[location.pk]),
    }
    subject = f"New review for {location.title}"
    text_body = render_to_string("emails/new_review.txt", context)
    html_body = render_to_string("emails/new_review.html", context)

    messages = []
    for user in get_review_recipients(review):
        message = EmailMultiAlternatives(subject=subject, body=text_body, to=[user.email])
        message.attach_alternative(html_body, "text/html")
        messages.append(message)

    connection = get_connection()
    return connection.send_messages(messages)

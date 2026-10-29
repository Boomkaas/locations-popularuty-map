from smtplib import SMTPException

from celery import shared_task

from .services import send_new_review_emails


@shared_task(autoretry_for=(SMTPException,), retry_backoff=True, max_retries=3)
def notify_new_review(review_id):
    return send_new_review_emails(review_id)

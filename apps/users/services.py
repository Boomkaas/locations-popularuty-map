from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()


def send_password_reset_email(email):
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    confirm_url = reverse("password-reset-confirm")
    message = (
        f"To set a new password, send a POST request to {confirm_url} "
        "with these values and your new password.\n\n"
        f"uid: {uid}\n"
        f"token: {token}"
    )

    send_mail(
        subject="Password reset",
        message=message,
        from_email=None,
        recipient_list=[user.email],
    )


def get_user_by_uid(uid):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def reset_password(user, new_password):
    user.set_password(new_password)
    user.save()

# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserIPHistory
from .utils import get_client_ip

@receiver(user_logged_in)
def log_user_ip_on_login(sender, request, user, **kwargs):
    ip_address = get_client_ip(request)

    # Avoid duplicate records for the same IP/user combination
    if not UserIPHistory.objects.filter(user=user, ip_address=ip_address).exists():
        UserIPHistory.objects.create(user=user, ip_address=ip_address)
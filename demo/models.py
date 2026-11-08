from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model

User = get_user_model()

class UserIPHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ip_history')
    ip_address = models.GenericIPAddressField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({self.created_at.strftime('%Y-%m-%d')})"

class Message(models.Model):
    delivered = models.BooleanField(default=False)

    message_text = models.TextField(default="")

    # 1. Allow sender to be null for Discord users who don't have a Django User account
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # 2. Add an optional text field for external sender names (e.g., "DiscordUser#1234")
    external_sender = models.CharField(max_length=100, blank=True, null=True)

    # 3. Store which channel it came from
    channel_id = models.CharField(max_length=50, blank=True, null=True)

    # 4. Add a timestamp for chronological sorting
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Displays the website user's username OR the external name
        sender_display = self.sender.username if self.sender else self.external_sender
        return f"{sender_display}: {self.message_text[:20]}"


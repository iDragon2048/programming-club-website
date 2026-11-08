from django.contrib import admin
from .models import Message, UserIPHistory
# Register your models here.
# admin.site.register(Message)
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "message_text")
    list_filter = ("channel_id",)

@admin.register(UserIPHistory)
class UserIPHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "created_at")
    list_filter = ("user",)
from django.contrib import admin
from .models import Tag, Assignment, UserAssignment, Meeting


class UserAssignmentInline(admin.TabularInline):
    model = UserAssignment
    extra = 1
    autocomplete_fields = ["user"]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "platform",
        "is_required",
        "due_date",
        "get_assigned_users_count",
        "created_at",
    )
    list_filter = ("platform", "is_required", "tags", "created_at", "due_date")
    search_fields = (
        "title",
        "description",
        "assigned_users__username",
        "assigned_users__email",
    )
    filter_horizontal = ("tags",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [UserAssignmentInline]

    fieldsets = (
        (
            "General Info",
            {
                "fields": (
                    "title",
                    "description",
                    "url",
                    "is_required",
                    "tags",
                )
            },
        ),
        (
            "Platform",
            {
                "fields": ("platform",)
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "due_date",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Assigned Users Count")
    def get_assigned_users_count(self, obj):
        return obj.assigned_users.count()


@admin.register(UserAssignment)
class UserAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "user",
        "status",
        "completed_at",
        "updated_at",
    )
    list_filter = ("status", "assignment__platform", "assignment__is_required")
    search_fields = (
        "assignment__title",
        "user__username",
        "user__email",
    )
    autocomplete_fields = ["user", "assignment"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("topic", "date", "get_attendance_count")
    list_filter = ("date",)
    search_fields = ("topic", "description", "attended_users__username")
    filter_horizontal = ("attended_users",)
    fieldsets = (
        (
            "Meeting Details",
            {
                "fields": (
                    "topic",
                    "date",
                    "description",
                    "attended_users",
                )
            },
        ),
        (
            "Recap Videos",
            {
                "fields": (
                    "recap_video_1",
                    "recap_video_2",
                    "recap_video_3",
                ),
                "classes": ("collapse",),  # Keeps video section collapsible
            },
        ),
    )

    @admin.display(description="Attendees")
    def get_attendance_count(self, obj):
        return obj.attended_users.count()

from django.contrib.admin.models import LogEntry

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    # Display columns in the admin list view
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')

    # Add filters on the right sidebar
    list_filter = ('action_flag', 'content_type', 'user')

    # Enable search functionality
    search_fields = ('object_repr', 'change_message')

    # Prevent users from editing or creating log entries manually
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

class Assignment(models.Model):
    class Platform(models.TextChoices):
        CODEWARS = "CW", "Codewars"
        CODINGAME = "CG", "CodinGame"
        PYCHARM = "PC", "PyCharm"
        WEBSITE = "WS", "Website"

    title = models.CharField(max_length=100, default='Programming Assignment')
    platform = models.CharField(max_length=2, choices=Platform.choices, default=Platform.PYCHARM)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    url = models.URLField(max_length=500, blank=True, help_text="Direct link to the problem")
    tags = models.ManyToManyField(Tag, related_name="assignments", blank=True)

    # ManyToMany using the explicit through model
    assigned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='UserAssignment',
        related_name='assignments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class UserAssignment(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NS", "Not Started"
        IN_PROGRESS = "IP", "In Progress"
        COMPLETE = "CP", "Complete"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_assignments")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="user_assignments")

    # Per-user specific fields
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.NOT_STARTED)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'assignment')

    def __str__(self):
        return f"{self.assignment.title} - {self.user.username} [{self.get_status_display()}]"

class Meeting(models.Model):
    topic = models.CharField(max_length=100, default="General Meeting")
    date = models.DateField(default=timezone.now)
    attended_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="attended_meetings", blank=True)
    description = models.TextField(blank=True)

    recap_video_1 = models.URLField(max_length=500, blank=True, help_text="Video on topics covered")
    recap_video_2 = models.URLField(max_length=500, blank=True, help_text="Video on topics covered")
    recap_video_3 = models.URLField(max_length=500, blank=True, help_text="Video on topics covered")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.topic} ({self.date})"
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class CodeFile(models.Model):
    title = models.CharField(max_length=100)
    code = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Custom user model that extends the default Django user model."""
    email = models.EmailField(
        unique=True
    )
    age = models.IntegerField(
        null=True,
        blank=True
    )
    username = models.CharField(
        default=None,
        max_length=150,
        null=True,
        blank=True,
        unique=True
    )

    def __str__(self):
        return self.username
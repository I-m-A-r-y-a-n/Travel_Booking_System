from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.email

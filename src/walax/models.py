import uuid
from django.db import models
from rest_framework.decorators import action


class WalaxModel(models.Model):
    class Meta:
        app_label = "walax"
        abstract = True

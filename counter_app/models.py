# counter_app/models.py

from django.db import models
from django.utils import timezone

class ViewCount(models.Model):
    total_views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Total Views: {self.total_views}"

class Visitor(models.Model):
    ip_address = models.GenericIPAddressField()
    device_type = models.CharField(max_length=50)
    visit_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visitor from {self.ip_address} on {self.device_type}"

class DailyViewCount(models.Model):
    date = models.DateField(unique=True)
    view_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Date: {self.date} - Views: {self.view_count}"

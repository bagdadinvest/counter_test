from django.db import models

class ViewCount(models.Model):
    total_views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Total Views: {self.total_views}"

class Visitor(models.Model):
    ip_address = models.GenericIPAddressField()
    device_type = models.CharField(max_length=50)
    visit_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"IP: {self.ip_address} - Device: {self.device_type} - Time: {self.visit_time}"

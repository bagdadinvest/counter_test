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


class HourlyViewCount(models.Model):
    date = models.DateField()
    hour = models.PositiveIntegerField()  # 0-23 representing the hour of the day
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('date', 'hour')
        verbose_name = 'Hourly View Count'
        verbose_name_plural = 'Hourly View Counts'

    def __str__(self):
        return f"{self.date} - {self.hour}:00 - {self.view_count} views"


class RequestLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=256, blank=True, null=True)
    path = models.CharField(max_length=256, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    headers = models.TextField(blank=True, null=True)
    referrer = models.CharField(max_length=256, blank=True, null=True)
    response_status = models.IntegerField(default=200, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    
    # New fields to store location data
    country = models.CharField(max_length=100, blank=True, null=True)  # Store country name or code
    city = models.CharField(max_length=100, blank=True, null=True)  # Store city name

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Request Log'
        verbose_name_plural = 'Request Logs'

    def __str__(self):
        return f"{self.timestamp} - {self.ip_address} - {self.path}"

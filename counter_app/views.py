# counter_app/views.py

from django.shortcuts import render
from .models import ViewCount, Visitor, DailyViewCount
from django.utils import timezone
from django.shortcuts import render
from .models import DailyViewCount
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

def dashboard(request):
    # Get the data for the past year
    today = timezone.now().date()
    one_year_ago = today - timedelta(days=365)
    view_counts = DailyViewCount.objects.filter(date__gte=one_year_ago).order_by('date')

    if view_counts.exists():
        dates = [vc.date.strftime('%Y-%m-%d') for vc in view_counts]
        counts = [vc.view_count for vc in view_counts]
    else:
        dates = []
        counts = []

    context = {
        'view_counts': view_counts,
        'dates': dates,
        'counts': counts,
    }
    return render(request, 'dashboard.html', context)


def get_client_ip(request):
    """Utility function to get the client's IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home(request):
    # Increment the total view count
    view_count, created = ViewCount.objects.get_or_create(pk=1)
    view_count.total_views += 1
    view_count.save()

    # Increment the daily view count
    today = timezone.now().date()
    daily_view_count, created = DailyViewCount.objects.get_or_create(date=today)
    daily_view_count.view_count += 1
    daily_view_count.save()

    # Get client IP and device type
    ip_address = get_client_ip(request)
    user_agent = request.user_agent
    if user_agent.is_mobile:
        device_type = 'Mobile'
    elif user_agent.is_tablet:
        device_type = 'Tablet'
    elif user_agent.is_pc:
        device_type = 'Desktop'
    else:
        device_type = 'Other'

    # Record visitor information
    Visitor.objects.create(ip_address=ip_address, device_type=device_type)

    context = {
        'total_views': view_count.total_views,
        'ip_address': ip_address,
        'device_type': device_type,
    }

    return render(request, 'home.html', context)

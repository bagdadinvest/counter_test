from django.shortcuts import render
from .models import ViewCount, Visitor

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

    # Get client IP
    ip_address = get_client_ip(request)

    # Use django-user-agents to get device type
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

    # Debugging output
    print("User Agent:", request.META.get('HTTP_USER_AGENT'))
    print("Detected Device Type:", device_type)

    return render(request, 'home.html', context)

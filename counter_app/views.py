import io
import base64
import csv
import json
import matplotlib
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.serializers import serialize
from django.utils import timezone
from datetime import timedelta
from .models import HourlyViewCount, RequestLog, ViewCount, Visitor  # Import missing models
from user_agents import parse
import matplotlib.pyplot as plt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

matplotlib.use('Agg')  # Use the Anti-Grain Geometry backend for non-GUI rendering

# Set up logging
logger = logging.getLogger(__name__)

##################################################################################################################################
########################################################## HOME ##################################################################
##################################################################################################################################


def home(request):
    """
    Home view that increments the view count for the current hour and displays recent request logs.
    """
    now = timezone.now()
    current_date = now.date()
    current_hour = now.hour  # 0-23 representing the hour of the day

    # Get or create the HourlyViewCount object for the current date and hour
    hourly_count, created = HourlyViewCount.objects.get_or_create(
        date=current_date,
        hour=current_hour,
        defaults={'view_count': 1}
    )

    if not created:
        # Increment the view count if it already exists
        hourly_count.view_count += 1
        hourly_count.save()

    # Retrieve recent request logs (e.g., last 20 entries)
    recent_requests = RequestLog.objects.all().order_by('-timestamp')[:20]

    # Retrieve filter parameters
    ip_filter = request.GET.get('ip', '').strip()
    device_filter = request.GET.get('device', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Apply filters to recent request logs
    if ip_filter:
        recent_requests = recent_requests.filter(ip_address__icontains=ip_filter)

    if device_filter:
        recent_requests = recent_requests.filter(user_agent__icontains=device_filter)

    if start_date:
        recent_requests = recent_requests.filter(timestamp__date__gte=start_date)

    if end_date:
        recent_requests = recent_requests.filter(timestamp__date__lte=end_date)

    # Annotate each request with device type using django-user-agents
    annotated_requests = []
    for req in recent_requests:
        user_agent_parsed = parse(req.user_agent)
        device_type = 'Desktop'  # Default to Desktop if not recognized

        if user_agent_parsed.is_mobile:
            device_type = 'Mobile'
        elif user_agent_parsed.is_tablet:
            device_type = 'Tablet'
        elif user_agent_parsed.is_pc:
            device_type = 'Desktop'
        else:
            device_type = 'Other'

        # Format headers as pretty-printed JSON
        headers_formatted = json.dumps(json.loads(req.headers), indent=2) if req.headers else 'N/A'

        # Append annotated request to the list
        annotated_requests.append({
            'timestamp': req.timestamp,
            'ip_address': req.ip_address,
            'device_type': device_type,
            'user_agent': req.user_agent or 'N/A',
            'path': req.path or 'N/A',
            'method': req.method or 'N/A',
            'referrer': req.referrer or 'N/A',
            'headers': headers_formatted,
            'response_status': req.response_status or 'N/A',
        })

    # Pagination settings for annotated requests
    page = request.GET.get('page', 1)
    paginator = Paginator(annotated_requests, 10)  # Show 10 logs per page

    try:
        recent_requests_page = paginator.page(page)
    except PageNotAnInteger:
        recent_requests_page = paginator.page(1)  # Show the first page
    except EmptyPage:
        recent_requests_page = paginator.page(paginator.num_pages)  # Show the last page if out of range

    # Debug statements for development (optional, remove in production)
    print(f"Hourly Count: {hourly_count.view_count}")
    print(f"Total Requests in Page: {len(recent_requests_page)}")

    # Context dictionary to pass to the template
    context = {
        'hourly_count': hourly_count,
        'recent_requests': recent_requests_page,
        'ip_filter': ip_filter,
        'device_filter': device_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'home.html', context)

##################################################################################################################################
########################################################## TOOLS #################################################################
##################################################################################################################################

def reset_database(request):
    """View to handle database reset."""
    if request.method == 'POST':
        # Delete all entries in the ViewCount, Visitor, and HourlyViewCount models
        ViewCount.objects.all().delete()
        Visitor.objects.all().delete()
        HourlyViewCount.objects.all().delete()
        RequestLog.objects.all().delete()  # Delete RequestLog entries as well
        return redirect(reverse('home'))  # Redirect back to home after reset

    return render(request, 'reset_confirmation.html')

def export_data(request, format_type):
    """View to handle exporting data in various formats."""
    if format_type == 'csv':
        # Export Visitor data to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="visitors.csv"'
        writer = csv.writer(response)
        writer.writerow(['IP Address', 'Device Type', 'Visit Time'])  # Write CSV header
        for visitor in Visitor.objects.all():
            writer.writerow([visitor.ip_address, visitor.device_type, visitor.visit_time])
        return response

    elif format_type == 'json':
        # Export Visitor data to JSON
        data = serialize('json', Visitor.objects.all())
        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="visitors.json"'
        return response

    # Add more formats if needed (e.g., XML)
    return HttpResponse("Unsupported format", status=400)

##################################################################################################################################
########################################################## DASHBOARD #############################################################
##################################################################################################################################

def dashboard(request):
    """
    Dashboard view that displays hourly views in a table and a bar chart.
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # Retrieve view counts within the past day
    view_counts = HourlyViewCount.objects.filter(date__gte=yesterday).order_by('date', 'hour')

    # Check if view counts data exists
    if view_counts.exists():
        # Prepare data for the table
        view_data = view_counts.values('date', 'hour', 'view_count')

        # Prepare data for the bar chart
        hourly_views = {}
        for vc in view_counts:
            hour_label = f"{vc.hour}:00"
            hourly_views[hour_label] = hourly_views.get(hour_label, 0) + vc.view_count

        # Prepare labels and sizes for the bar chart
        labels = list(hourly_views.keys())
        sizes = list(hourly_views.values())

        # Generate the bar chart using Matplotlib
        plt.figure(figsize=(10, 6))
        plt.bar(labels, sizes, color='skyblue')
        plt.xlabel('Hour of the Day')
        plt.ylabel('View Count')
        plt.title('Hourly View Distribution (Past 24 Hours)')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the bar chart to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        # Encode the image to base64 to embed in HTML
        image_png = buf.getvalue()
        bar_chart = base64.b64encode(image_png).decode('utf-8')
        buf.close()
    else:
        view_data = []
        bar_chart = None

    context = {
        'view_data': view_data,  # Data for the HTML table
        'bar_chart': bar_chart,  # Base64-encoded bar chart image
    }
    return render(request, 'dashboard.html', context)

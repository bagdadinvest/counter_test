import io
import base64
import csv
import json
import logging
import matplotlib
import matplotlib.pyplot as plt
from ipwhois import IPWhois
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.serializers import serialize
from django.utils import timezone
from datetime import timedelta
from .models import HourlyViewCount, RequestLog, ViewCount, Visitor
from user_agents import parse
from django.conf import settings 
from ipaddress import ip_address, IPv4Address
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .geoip import update_request_log_with_location_data
# Configure matplotlib to use the non-GUI backend
matplotlib.use('Agg')

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
        hourly_count.view_count += 1
        hourly_count.save()

    # Retrieve Request Logs
    recent_requests = RequestLog.objects.all().order_by('-timestamp')

    # Retrieve Filter Parameters from the Request
    ip_filter = request.GET.get('ip', '').strip()
    device_filter = request.GET.get('device', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Apply Filters to the QuerySet
    if ip_filter:
        recent_requests = recent_requests.filter(ip_address__icontains=ip_filter)

    if device_filter:
        recent_requests = recent_requests.filter(user_agent__icontains=device_filter)

    if start_date:
        recent_requests = recent_requests.filter(timestamp__date__gte=start_date)

    if end_date:
        recent_requests = recent_requests.filter(timestamp__date__lte=end_date)

    # Annotate and Prepare Data for the Table with Location and ASN Information
    annotated_requests = []
    for req in recent_requests:
        update_request_log_with_location_data(req)  # Update the location and ASN information

        user_agent_parsed = parse(req.user_agent)
        device_type = 'Desktop' if user_agent_parsed.is_pc else 'Mobile' if user_agent_parsed.is_mobile else 'Tablet' if user_agent_parsed.is_tablet else 'Other'

        headers_formatted = json.dumps(json.loads(req.headers), indent=2) if req.headers else 'N/A'

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
            'country': req.country,  # Include country
            'city': req.city,  # Include city
            'asn': req.autonomous_system_number,  # Include ASN number
            'asn_organization': req.autonomous_system_organization,  # Include ASN organization
        })

    # Apply Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(annotated_requests, 10)

    try:
        recent_requests_page = paginator.page(page)
    except PageNotAnInteger:
        recent_requests_page = paginator.page(1)
    except EmptyPage:
        recent_requests_page = paginator.page(paginator.num_pages)

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
        # Export RequestLog data to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="request_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'IP Address', 'Device Type', 'User Agent', 'Path', 'Method', 'Referrer', 'Status', 'Country', 'City'])  # CSV Header
        for req in RequestLog.objects.all():
            try:
                # Lookup location data for each request
                obj = IPWhois(req.ip_address)
                result = obj.lookup_rdap()
                country = result.get('asn_country_code', 'N/A')
                city = result.get('network', {}).get('city', 'N/A')
            except Exception as e:
                country = 'Unknown'
                city = 'Unknown'

            writer.writerow([req.timestamp, req.ip_address, req.user_agent, req.path, req.method, req.referrer, req.response_status, country, city])
        return response

    elif format_type == 'json':
        # Export RequestLog data to JSON
        data = serialize('json', RequestLog.objects.all())
        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="request_logs.json"'
        return response

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

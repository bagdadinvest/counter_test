import json
import logging
from .models import RequestLog

logger = logging.getLogger('counter_app.middleware')

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Extract request data
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            path = request.path
            method = request.method
            headers = self.get_request_headers(request)
            referrer = request.META.get('HTTP_REFERER', 'N/A')

            # Create a RequestLog entry with a temporary response_status
            request_log = RequestLog.objects.create(
                ip_address=ip_address,
                user_agent=user_agent,
                path=path,
                method=method,
                headers=json.dumps(headers),
                referrer=referrer,
                response_status=200  # Temporary value; will update after response
            )

            logger.debug(f"Logged request: {request_log}")

        except Exception as e:
            logger.error(f"Error logging request: {e}")
            request_log = None

        # Continue processing the request
        response = self.get_response(request)

        if request_log:
            try:
                # Update the response_status with the actual status code
                request_log.response_status = response.status_code
                request_log.save()
                logger.debug(f"Updated response_status to {response.status_code} for log ID {request_log.id}")
            except Exception as e:
                logger.error(f"Error updating response status: {e}")

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip

    def get_request_headers(self, request):
        headers = {}
        for header, value in request.META.items():
            if header.startswith('HTTP_'):
                header_name = header[5:].replace('_', '-').title()
                headers[header_name] = value
        return headers

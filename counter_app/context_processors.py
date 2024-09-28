# counter_app/context_processors.py

from django.utils import timezone

def current_year(request):
    return {'current_year': timezone.now().year}

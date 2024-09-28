from django.contrib import admin
from django.urls import path, include  # include is needed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('counter_app.urls')),  # Include the app's URLs
]

from django.contrib import admin
from django.urls import path, include  # include is needed
from django.conf import settings  # Import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('counter_app.urls')),  # Include the app's URLs
]
if settings.DEBUG:  # Only include Debug Toolbar when in DEBUG mode
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

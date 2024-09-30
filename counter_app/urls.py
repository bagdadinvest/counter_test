from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reset/', views.reset_database, name='reset_database'),  # Reset button route
    path('export/<str:format_type>/', views.export_data, name='export_data'),  # Export button route
]


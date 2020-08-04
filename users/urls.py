"""Defines URL patterns for users"""

from django.urls import path, include
from . import views

app_name = 'users'
urlpatterns = [
    # Include default auth urls.
    path('', include('django.contrib.auth.urls')),

    # Registration page.
    path('register/', views.register, name='register'),

    # Profile page.
    path('profile/', views.profile, name='profile'),

    # Profile page.
    path('update/', views.update_profile, name='update'),
    ]

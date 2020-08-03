"""Defines URL patterns for users"""

from django.urls import path, include
from . import views

app_name = 'fixpol'

urlpatterns = [
    # Home page
    path('', views.index, name='index'),

    # Page that shows all locations.
    path('locations/', views.locations, name='locations'),
    ]



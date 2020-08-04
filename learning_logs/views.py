from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404


# Create your views here.


def index(request):
    """The home page for Learning Log."""
    return render(request, 'learning_logs/index.html')



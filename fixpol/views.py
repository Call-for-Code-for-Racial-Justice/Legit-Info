from django.shortcuts import render

# Create your views here.
def index(request):
    """The home page for Fix Politics."""
    return render(request, 'index.html')

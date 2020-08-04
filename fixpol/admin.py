from django.contrib import admin

# Register your models here.
from .models import Location
from .models import Impact
from .models import Profile

admin.site.register(Location)
admin.site.register(Impact)
admin.site.register(Profile)

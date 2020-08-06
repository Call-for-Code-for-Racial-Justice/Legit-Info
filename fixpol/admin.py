from django.contrib import admin

# Register your models here.
from .models import Location, Impact, Criteria

admin.site.register(Location)
admin.site.register(Impact)
admin.site.register(Criteria)

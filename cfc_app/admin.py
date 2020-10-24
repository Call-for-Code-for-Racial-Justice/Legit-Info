from django.contrib import admin

# Register your models here.
from .models import Location, Impact, Criteria, Law, Hash

admin.site.register(Location)
admin.site.register(Impact)
admin.site.register(Criteria)
admin.site.register(Law)
admin.site.register(Hash)

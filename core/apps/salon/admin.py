from django.contrib import admin

from .models import Salon, OpeningHours, SalonMedia, Service

admin.site.register(Salon)
admin.site.register(OpeningHours)
admin.site.register(SalonMedia)
admin.site.register(Service)

from django.contrib import admin

from .models import (
    Salon,
    OpeningHours,
    SalonMedia,
    Service,
    Product,
    Employee,
    Chair,
    Booking,
)

admin.site.register(Salon)
admin.site.register(OpeningHours)
admin.site.register(SalonMedia)
admin.site.register(Service)
admin.site.register(Product)
admin.site.register(Employee)
admin.site.register(Chair)
admin.site.register(Booking)

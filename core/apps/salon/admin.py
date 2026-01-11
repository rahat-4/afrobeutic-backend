from django.contrib import admin

from .models import (
    Salon,
    OpeningHours,
    SalonMedia,
    ServiceCategory,
    ServiceSubCategory,
    Service,
    ProductCategory,
    ProductSubCategory,
    Product,
    Employee,
    Chair,
    Booking,
    Customer,
)

admin.site.register(Salon)
admin.site.register(OpeningHours)
admin.site.register(SalonMedia)
admin.site.register(ServiceCategory)
admin.site.register(ServiceSubCategory)
admin.site.register(Service)
admin.site.register(ProductCategory)
admin.site.register(ProductSubCategory)
admin.site.register(Product)
admin.site.register(Employee)
admin.site.register(Chair)
admin.site.register(Booking)
admin.site.register(Customer)

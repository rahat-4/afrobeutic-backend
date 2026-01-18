from django.contrib import admin

from .models import PricingPlan, Subscription, PaymentCard, PaymentTransaction

admin.site.register(Subscription)
admin.site.register(PaymentCard)
admin.site.register(PaymentTransaction)
admin.site.register(PricingPlan)

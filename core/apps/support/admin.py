from django.contrib import admin

from .models import SupportTicket, AccountSupportTicket

# Register your models here.
admin.site.register(SupportTicket)
admin.site.register(AccountSupportTicket)

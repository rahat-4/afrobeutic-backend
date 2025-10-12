from django.contrib import admin

from .models import Account, AccountMembership, AccountInvitation, User

admin.site.register(User)
admin.site.register(Account)
admin.site.register(AccountMembership)
admin.site.register(AccountInvitation)

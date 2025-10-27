from django.urls import path, include

urlpatterns = [
    path("/auth", include("api.urls.auth")),
    path("/accounts", include("api.urls.accounts")),
    path("/salons", include("api.urls.salons")),
    path("/customers", include("api.urls.customers")),
]

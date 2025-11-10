from django.urls import path, include

urlpatterns = [
    path("/auth", include("api.urls.auth")),
    path("/accounts", include("api.urls.accounts")),
    path("/salons", include("api.urls.salons")),
    path("/customers", include("api.urls.customers")),
    path("/categories", include("common.urls")),
    path("/support-tickets", include("api.urls.supports")),
    path("/admin", include("api.urls.admin")),
]

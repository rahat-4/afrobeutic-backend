from django.urls import path, include

urlpatterns = [
    path("", include("common.urls")),
    path("/auth", include("api.urls.auth")),
    path("/accounts", include("api.urls.accounts")),
    path("/salons", include("api.urls.salons")),
    path("/customers", include("api.urls.customers")),
    path("/leads", include("api.urls.leads")),
    path("/support", include("api.urls.supports")),
    path("/config", include("api.urls.config")),
    path("/admin", include("api.urls.admin")),
]

from django.urls import path, include

urlpatterns = [
    path("/auth", include("api.urls.auth")),
    path("/accounts", include("api.urls.accounts")),
    path("/accounts/<uuid:account_uid>/salons", include("api.urls.salons")),
]

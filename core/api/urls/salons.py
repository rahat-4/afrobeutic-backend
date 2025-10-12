from django.urls import path

from ..views.salons import SalonListView, SalonDetailView

urlpatterns = [
    path("", SalonListView.as_view(), name="salon.list"),
    path(
        "/<uuid:salon_uid>",
        SalonDetailView.as_view(),
        name="salon.detail",
    ),
]

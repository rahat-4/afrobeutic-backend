from django.urls import path

from ..views.config import (
    TwilioConfListView,
    TwilioConfDetailView,
)

urlpatterns = [
    path(
        "/twilio/<uuid:twilio_uid>",
        TwilioConfDetailView.as_view(),
        name="config.twilio-detail",
    ),
    path("/twilio", TwilioConfListView.as_view(), name="config.twilio-list"),
]

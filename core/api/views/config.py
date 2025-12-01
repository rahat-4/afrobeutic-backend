from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from apps.thirdparty.models import TwilioConf

from common.permissions import IsOwnerOrAdmin

from ..serializers.config import TwilioConfSerializer


class TwilioConfListView(ListCreateAPIView):
    serializer_class = TwilioConfSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        account = self.request.account
        return TwilioConf.objects.filter(account=account)

    def perform_create(self, serializer):
        serializer.save(account=self.request.account)


class TwilioConfDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TwilioConfSerializer
    permission_classes = [IsOwnerOrAdmin]
    lookup_url_kwarg = "twilio_uid"

    def get_object(self):
        account = self.request.account
        twilio_uid = self.kwargs.get(self.lookup_url_kwarg)
        return TwilioConf.objects.get(account=account, uid=twilio_uid)

from rest_framework.generics import ListAPIView

from apps.thirdparty.models import WhatsappChatbotConfig

from common.permissions import IsOwnerOrAdminOrStaff

from ..serializers.chatbots import WhatsappChatbotConfigSerializer


class WhatsappChatbotConfigListAPIView(ListAPIView):
    serializer_class = WhatsappChatbotConfigSerializer
    permission_classes = [IsOwnerOrAdminOrStaff]

    def get_queryset(self):
        account = self.request.account
        return WhatsappChatbotConfig.objects.filter(account=account)

from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView

from apps.thirdparty.models import WhatsappChatbotConfig, WhatsappChatbotMessageLog

from common.permissions import IsOwnerOrAdmin

from ..serializers.config import WhatsappChatbotConfigSerializer, WhatsappChatbotMessageLogSerializer


class WhatsappChatbotListView(ListCreateAPIView):
    serializer_class = WhatsappChatbotConfigSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class WhatsappChatbotDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = WhatsappChatbotConfigSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        salon_id = self.kwargs["salon_id"]
        return WhatsappChatbotConfig.objects.get(salon_id=salon_id)

class WhatsappChatbotMessageListView(ListAPIView):
    serializer_class = WhatsappChatbotMessageLogSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return WhatsappChatbotMessageLog.objects.filter(
            chatbot__salon_id=self.kwargs["salon_id"]
        ).order_by("created_at")

from rest_framework import serializers

from apps.support.models import SupportTicket

from common.models import Media
from common.serializers import MediaSerializer


class SupportTicketSerializer(serializers.ModelSerializer):
    images = MediaSerializer(many=True, read_only=True, source="support_ticket_images")
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = SupportTicket
        fields = [
            "uid",
            "level",
            "topic",
            "subject",
            "queries",
            "status",
            "images",
            "uploaded_images",
            "created_at",
        ]

    def validate_uploaded_images(self, value):
        """
        Ensure no more than 3 images are uploaded.
        """
        if len(value) > 3:
            raise serializers.ValidationError("You can upload a maximum of 3 images.")
        return value

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        support_ticket = SupportTicket.objects.create(**validated_data)

        for image in uploaded_images:
            Media.objects.create(support_ticket=support_ticket, image=image)

        return support_ticket

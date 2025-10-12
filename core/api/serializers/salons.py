from datetime import datetime, timedelta, time

from django.db import transaction

from rest_framework import serializers

from apps.authentication.models import AccountMembership, AccountMembershipRole
from apps.salon.models import Salon, OpeningHours


class OpeningHoursSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpeningHours
        exclude = ["salon", "created_at", "updated_at"]


class SalonSerializer(serializers.ModelSerializer):
    opening_hours = OpeningHoursSerializer(many=True, required=False)

    class Meta:
        model = Salon
        fields = [
            "uid",
            "name",
            "salon_type",
            "email",
            "phone",
            "website",
            "street",
            "city",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "status",
            "opening_hours",
        ]

    def validate_status(self, value):
        if self.instance and self.instance.status != value:
            # Status is being changed
            request = self.context.get("request")
            if request and request.user:
                is_owner = AccountMembership.objects.filter(
                    user=request.user,
                    account=self.instance.account,
                    role=AccountMembershipRole.OWNER,
                ).exists()

                if not is_owner:
                    raise serializers.ValidationError(
                        "Only account owners can change the salon status."
                    )
        return value

    def validate(self, attrs):
        opening_hours = attrs.get("opening_hours", [])
        errors = {}

        # Validate each day's opening hours
        opening_hours_errors = {}

        for _, day in enumerate(opening_hours):
            day_errors = {}

            is_closed = day.get("is_closed", False)

            # Default times to 00:00:00 if not provided
            opening_start = day.get("opening_start_time") or time(0, 0)
            opening_end = day.get("opening_end_time") or time(0, 0)
            break_start = day.get("break_start_time") or time(0, 0)
            break_end = day.get("break_end_time") or time(0, 0)

            if (
                any(
                    t == time(0, 0)
                    for t in [opening_start, opening_end, break_start, break_end]
                )
                and not is_closed
            ):
                opening_hours_errors[f"{day['day'].capitalize()}"] = [
                    "All fields must be provided unless the day is marked as closed."
                ]
            elif not is_closed:
                # Validate opening times
                if opening_start >= opening_end:
                    opening_hours_errors[f"{day['day'].capitalize()}"] = [
                        "Opening start time must be before end time."
                    ]

                # Validate break times if not all zero
                if (break_start != time(0, 0)) or (break_end != time(0, 0)):
                    if not (opening_start <= break_start < break_end <= opening_end):
                        opening_hours_errors[f"{day['day'].capitalize()}"] = [
                            "Break time must be within the opening hours range."
                        ]
                    else:
                        break_duration = datetime.combine(
                            datetime.today(), break_end
                        ) - datetime.combine(datetime.today(), break_start)

                        if break_duration > timedelta(hours=2):
                            opening_hours_errors[f"{day['day'].capitalize()}"] = [
                                "Break time cannot exceed 2 hours."
                            ]

            if day_errors:
                opening_hours_errors[f"{day['day'].capitalize()}"] = day_errors

        if opening_hours_errors:
            errors["opening_hours"] = opening_hours_errors

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            opening_hours = validated_data.pop("opening_hours", [])
            salon = Salon.objects.create(**validated_data)

            for opening_hour in opening_hours:
                OpeningHours.objects.create(salon=salon, **opening_hour)
            return salon

    def update(self, instance, validated_data):
        with transaction.atomic():
            opening_hours = validated_data.pop("opening_hours", [])

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            # Opening Hours
            if opening_hours != []:
                OpeningHours.objects.filter(salon=instance).delete()
                for opening_hour in opening_hours:
                    OpeningHours.objects.create(salon=instance, **opening_hour)
            return instance

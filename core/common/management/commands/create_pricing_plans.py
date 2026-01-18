from django.core.management.base import BaseCommand

from apps.billing.choices import AccountCategory, PlanType
from apps.billing.models import PricingPlan


class Command(BaseCommand):
    help = "Seed initial pricing plans"

    def handle(self, *args, **kwargs):
        plans = [
            # Individual Stylist Plans
            {
                "account_category": AccountCategory.INDIVIDUAL_STYLIST,
                "plan_type": PlanType.GOLD,
                "price": 10.00,
                "salon_count": 1,
                "whatsapp_chatbot_count": 0,
                "whatsapp_messages_limit": 0,
                "has_broadcasting": False,
                "broadcasting_message_limit": 0,
                "description": "Perfect for individual stylists starting out",
            },
            {
                "account_category": AccountCategory.INDIVIDUAL_STYLIST,
                "plan_type": PlanType.PLATINUM,
                "price": 30.00,
                "salon_count": 1,
                "whatsapp_chatbot_count": 1,
                "whatsapp_messages_limit": 2000,
                "has_broadcasting": True,
                "broadcasting_message_limit": 100,
                "description": "Advanced features for professional stylists",
            },
            {
                "account_category": AccountCategory.INDIVIDUAL_STYLIST,
                "plan_type": PlanType.CUSTOM,
                "price": 0.00,
                "salon_count": 1,
                "whatsapp_chatbot_count": 0,
                "whatsapp_messages_limit": 0,
                "has_broadcasting": False,
                "broadcasting_message_limit": 0,
                "description": "Custom plan based on your specific needs",
            },
            # Salon Shop Plans
            {
                "account_category": AccountCategory.SALON_SHOP,
                "plan_type": PlanType.GOLD,
                "price": 30.00,
                "salon_count": 1,
                "whatsapp_chatbot_count": 1,
                "whatsapp_messages_limit": 2000,
                "has_broadcasting": True,
                "broadcasting_message_limit": 150,
                "description": "Great for small salon businesses",
            },
            {
                "account_category": AccountCategory.SALON_SHOP,
                "plan_type": PlanType.PLATINUM,
                "price": 70.00,
                "salon_count": 3,
                "whatsapp_chatbot_count": 3,
                "whatsapp_messages_limit": 2000,
                "has_broadcasting": True,
                "broadcasting_message_limit": 300,
                "description": "Perfect for multi-location salons",
            },
            {
                "account_category": AccountCategory.SALON_SHOP,
                "plan_type": PlanType.CUSTOM,
                "price": 0.00,
                "salon_count": 1,
                "whatsapp_chatbot_count": 0,
                "whatsapp_messages_limit": 0,
                "has_broadcasting": False,
                "broadcasting_message_limit": 0,
                "description": "Custom plan tailored to your salon network",
            },
        ]

        for plan_data in plans:
            plan, created = PricingPlan.objects.update_or_create(
                account_category=plan_data["account_category"],
                plan_type=plan_data["plan_type"],
                defaults=plan_data,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {plan}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated: {plan}"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded pricing plans!"))

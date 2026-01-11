from django.core.management.base import BaseCommand
from apps.salon.models import ServiceCategory, ServiceSubCategory


SERVICE_CATEGORIES = {
    "HAIR_SERVICES": [
        "Haircuts & styling",
        "Hair coloring",
        "Braiding, locs, protective styles",
        "Hair treatments (keratin, scalp care)",
        "Wig & Weave",
    ],
    "HAIR_REMOVAL_SERVICES": [
        "Waxing",
        "Threading",
        "Sugaring",
        "Laser hair removal (licensed)",
    ],
    "BRIDAL_AND_MAKEUP_SERVICES": [
        "Bridal makeup",
        "Party / event makeup",
        "Airbrush / HD makeup",
        "Groom makeup & styling",
    ],
    "MENS_GROOMING_SERVICES": [
        "Men’s haircut & styling",
        "Beard trim & shave",
        "Groom facial",
        "Scalp treatments",
    ],
    "SKIN_OR_FACIAL_SERVICES": [
        "Basic & advanced facials",
        "Acne & anti-aging treatments",
        "Cleansing, exfoliation, masks",
        "Chemical peels (licensed)",
    ],
    "NAIL_SERVICES": [
        "Manicure",
        "Pedicure",
        "Gel / acrylic nails",
        "Nail art & extensions",
    ],
    "MESSAGE_AND_BODY_SERVICES": [
        "Head, neck & shoulder massage",
        "Full body massage",
        "Body scrubs & wraps",
        "Relaxation therapies",
    ],
    "EYEBROW_AND_EYELASH_SERVICES": [
        "Brow shaping & tinting",
        "Eyelash extensions",
        "Lash lifts",
        "Microblading (licensed)",
    ],
    "OTHER_SERVICES": [],
}


class Command(BaseCommand):
    help = "Create service categories and sub-categories if not exists"

    def handle(self, *args, **options):
        for category_name, sub_categories in SERVICE_CATEGORIES.items():
            category, created = ServiceCategory.objects.get_or_create(
                name=category_name
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created service category: {category_name}")
                )

            for sub_name in sub_categories:
                _, sub_created = ServiceSubCategory.objects.get_or_create(
                    category=category, name=sub_name, defaults={"is_custom": False}
                )

                if sub_created:
                    self.stdout.write(f"  └─ Created sub-category: {sub_name}")

        self.stdout.write(self.style.SUCCESS("Service categories setup complete ✅"))

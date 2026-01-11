from django.core.management.base import BaseCommand
from apps.salon.models import ProductCategory, ProductSubCategory


PRODUCT_CATEGORIES = {
    "HAIR_CARE_PRODUCTS": [
        "Shampoo",
        "Conditioner",
        "Hair masks & deep conditioners",
        "Hair oils & serums",
        "Styling products (gel, mousse, cream, , spray)",
        "Scalp care products",
        "Hair color products (retail)",
        "Wig & weave care products",
    ],
    "SKIN_CARE_PRODUCTS": [
        "Facial cleansers",
        "Toners",
        "Moisturizers",
        "Serums & treatments",
        "Face masks & exfoliators",
        "Sunscreen",
        "Acne & anti-aging products",
    ],
    "MAKEUP_PRODUCTS": [
        "Face makeup (foundation, concealer, powder)",
        "Eye makeup (mascara, eyeliner, eyeshadow)",
        "Lip products (lipstick, gloss, liner)",
        "Makeup palettes & kits",
        "Bridal / professional makeup products",
        "Makeup removers",
    ],
    "NAIL_CARE_PRODUCTS": [
        "Nail polish",
        "Gel & acrylic systems",
        "Nail treatments (strengtheners, cuticle oil)",
        "Nail art supplies",
        "Nail care tools",
    ],
    "MENS_GROOMING_PRODUCTS": [
        "Beard oils & balms",
        "Shaving creams & gels",
        "Aftershave & cologne",
        "Hair styling products for men",
        "Grooming kits",
    ],
    "BODY_CARE_PRODUCTS": [
        "Body wash & soaps",
        "Body scrubs & exfoliators",
        "Body lotions & creams",
        "Massage oils",
        "Aromatherapy products",
    ],
    "HAIR_REMOVAL_PRODUCTS": [
        "Wax (hard, soft)",
        "Pre-wax & after-wax products",
        "Sugaring paste",
        "Hair removal creams",
        "Laser care products (post-treatment)",
    ],
    "TOOLS_AND_ACCESSORIES": [
        "Hair tools (dryers, straighteners, curlers)",
        "Brushes & combs",
        "Makeup tools (brushes, sponges)",
        "Nail tools",
        "Disposable salon supplies",
    ],
    "SALON_RETAIL_AND_GIFT_PRODUCTS": [
        "Gift cards & vouchers",
        "Travel-size products",
        "Product bundles & kits",
    ],
    "OTHER_PRODUCTS": [],
}


class Command(BaseCommand):
    help = "Create product categories and sub-categories if not exists"

    def handle(self, *args, **options):
        for category_name, sub_categories in PRODUCT_CATEGORIES.items():
            category, created = ProductCategory.objects.get_or_create(
                name=category_name
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created product category: {category_name}")
                )

            for sub_name in sub_categories:
                _, sub_created = ProductSubCategory.objects.get_or_create(
                    category=category, name=sub_name, defaults={"is_custom": False}
                )

                if sub_created:
                    self.stdout.write(f"  └─ Created sub-category: {sub_name}")

        self.stdout.write(self.style.SUCCESS("Product categories setup complete ✅"))

from django.core.management.base import BaseCommand

from catalog.models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeValue,
)


class Command(BaseCommand):
    help = "Seed the catalog with sample categories, brands, and products"

    def handle(self, *args, **options):
        self.stdout.write("Seeding catalog...")

        # ── Categories ─────────────────────────────────────
        laptops, _ = Category.objects.get_or_create(
            name="Laptops", slug="laptops", defaults={"icon": "fa-laptop", "order": 1}
        )
        gaming_laptops, _ = Category.objects.get_or_create(
            name="Gaming Laptops",
            slug="gaming-laptops",
            defaults={"parent": laptops, "order": 1},
        )
        office_laptops, _ = Category.objects.get_or_create(
            name="Office Laptops",
            slug="office-laptops",
            defaults={"parent": laptops, "order": 2},
        )
        components, _ = Category.objects.get_or_create(
            name="Components",
            slug="components",
            defaults={"icon": "fa-microchip", "order": 2},
        )
        gpu, _ = Category.objects.get_or_create(
            name="Graphics Cards",
            slug="graphics-cards",
            defaults={"parent": components, "order": 1},
        )
        cpu, _ = Category.objects.get_or_create(
            name="Processors",
            slug="processors",
            defaults={"parent": components, "order": 2},
        )
        peripherals, _ = Category.objects.get_or_create(
            name="Peripherals",
            slug="peripherals",
            defaults={"icon": "fa-keyboard", "order": 3},
        )
        monitors, _ = Category.objects.get_or_create(
            name="Monitors",
            slug="monitors",
            defaults={"parent": peripherals, "order": 1},
        )

        self.stdout.write(
            self.style.SUCCESS(f"  Categories: {Category.objects.count()} created")
        )

        # ── Brands ─────────────────────────────────────────
        brands_data = [
            ("ASUS", "asus"),
            ("Logitech", "logitech"),
            ("NVIDIA", "nvidia"),
            ("Intel", "intel"),
            ("Samsung", "samsung"),
            ("LG", "lg"),
        ]
        for name, slug in brands_data:
            Brand.objects.get_or_create(name=name, slug=slug)
        self.stdout.write(
            self.style.SUCCESS(f"  Brands: {Brand.objects.count()} created")
        )

        # ── Attributes ─────────────────────────────────────
        ram, _ = ProductAttribute.objects.get_or_create(name="RAM", unit="GB")
        storage, _ = ProductAttribute.objects.get_or_create(name="Storage", unit="GB")
        screen, _ = ProductAttribute.objects.get_or_create(
            name="Screen Size", unit="inch"
        )
        resolution, _ = ProductAttribute.objects.get_or_create(name="Resolution")
        cores, _ = ProductAttribute.objects.get_or_create(name="Cores")
        vram, _ = ProductAttribute.objects.get_or_create(name="VRAM", unit="GB")
        refresh, _ = ProductAttribute.objects.get_or_create(
            name="Refresh Rate", unit="Hz"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"  Attributes: {ProductAttribute.objects.count()} created"
            )
        )

        # ── Products ───────────────────────────────────────
        asus = Brand.objects.get(slug="asus")
        nvidia = Brand.objects.get(slug="nvidia")
        intel = Brand.objects.get(slug="intel")
        samsung = Brand.objects.get(slug="samsung")
        logitech = Brand.objects.get(slug="logitech")
        lg = Brand.objects.get(slug="lg")

        products_data = [
            {
                "title": "ASUS ROG Strix G16 (2024)",
                "category": gaming_laptops,
                "brand": asus,
                "description": "16-inch gaming laptop with Intel Core i9-14900HX and NVIDIA RTX 4070. "
                "Features a 165Hz display, 16GB DDR5 RAM, and 1TB SSD.",
                "base_price": 52000000,
                "discount_price": 48500000,
                "sku": "ASUS-ROG-G16-001",
                "is_featured": True,
                "warranty_months": 24,
                "attrs": {
                    ram: "16",
                    storage: "1000",
                    screen: "16",
                    resolution: "2560x1600",
                    refresh: "165",
                },
            },
            {
                "title": "ASUS VivoBook 15 X1504ZA",
                "category": office_laptops,
                "brand": asus,
                "description": "15.6-inch thin and light laptop for everyday use. "
                "Intel Core i5-1235U, 8GB RAM, 512GB SSD.",
                "base_price": 23500000,
                "sku": "ASUS-VIV-15-001",
                "is_featured": False,
                "warranty_months": 18,
                "attrs": {
                    ram: "8",
                    storage: "512",
                    screen: "15.6",
                    resolution: "1920x1080",
                },
            },
            {
                "title": "ASUS TUF Gaming A15",
                "category": gaming_laptops,
                "brand": asus,
                "description": "15.6-inch durable gaming laptop. AMD Ryzen 7 7735HS, "
                "NVIDIA RTX 4060, 16GB RAM, 512GB SSD.",
                "base_price": 38000000,
                "discount_price": 35500000,
                "sku": "ASUS-TUF-A15-001",
                "is_featured": True,
                "warranty_months": 24,
                "attrs": {
                    ram: "16",
                    storage: "512",
                    screen: "15.6",
                    resolution: "1920x1080",
                    refresh: "144",
                },
            },
            {
                "title": "NVIDIA GeForce RTX 4070 Ti SUPER",
                "category": gpu,
                "brand": nvidia,
                "description": "High-end desktop graphics card. 16GB GDDR6X memory, "
                "DLSS 3.0, ray tracing support.",
                "base_price": 62000000,
                "sku": "NV-RTX4070TIS-001",
                "is_featured": True,
                "warranty_months": 36,
                "attrs": {vram: "16", cores: "8448"},
            },
            {
                "title": "Intel Core i7-14700K",
                "category": cpu,
                "brand": intel,
                "description": "20-core desktop processor (8P + 12E). Base clock 3.4GHz, "
                "boost up to 5.6GHz. Unlocked for overclocking.",
                "base_price": 18500000,
                "sku": "INT-i7-14700K-001",
                "is_featured": False,
                "warranty_months": 36,
                "attrs": {cores: "20"},
            },
            {
                "title": "Samsung Odyssey G5 27-inch",
                "category": monitors,
                "brand": samsung,
                "description": "27-inch WQHD gaming monitor with 165Hz refresh rate "
                "and 1ms response time. VA panel, HDR10.",
                "base_price": 12000000,
                "discount_price": 10500000,
                "sku": "SAM-G5-27-001",
                "is_featured": True,
                "warranty_months": 36,
                "attrs": {screen: "27", resolution: "2560x1440", refresh: "165"},
            },
            {
                "title": "Logitech G Pro X Superlight 2",
                "category": peripherals,
                "brand": logitech,
                "description": "Ultra-lightweight wireless gaming mouse. Only 60g. "
                "HERO 2 sensor, 32K DPI.",
                "base_price": 5800000,
                "sku": "LOGI-GPX2-001",
                "is_featured": False,
                "warranty_months": 24,
                "attrs": {},
            },
            {
                "title": "LG 27GP850-B UltraGear",
                "category": monitors,
                "brand": lg,
                "description": "27-inch Nano IPS gaming monitor. WQHD, 165Hz (OC 180Hz), "
                "1ms GtG, HDR400, G-Sync Compatible.",
                "base_price": 15000000,
                "discount_price": 13800000,
                "sku": "LG-27GP850-001",
                "is_featured": True,
                "warranty_months": 24,
                "attrs": {screen: "27", resolution: "2560x1440", refresh: "180"},
            },
        ]

        for pdata in products_data:
            attrs = pdata.pop("attrs")
            product, created = Product.objects.get_or_create(
                sku=pdata["sku"],
                defaults={**pdata, "status": "active"},
            )
            if created:
                for attr, value in attrs.items():
                    ProductAttributeValue.objects.get_or_create(
                        product=product, attribute=attr, defaults={"value": value}
                    )

        self.stdout.write(
            self.style.SUCCESS(f"  Products: {Product.objects.count()} created")
        )
        self.stdout.write(self.style.SUCCESS("Catalog seeded successfully!"))

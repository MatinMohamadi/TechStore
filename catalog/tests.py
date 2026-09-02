from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Brand, Category, Product, ProductAttribute, ProductAttributeValue


class CategoryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.parent = Category.objects.create(name="Laptops", slug="laptops")
        self.child = Category.objects.create(
            name="Gaming Laptops", slug="gaming-laptops", parent=self.parent
        )

    def test_list_categories(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_category_detail(self):
        response = self.client.get(f"/api/categories/{self.parent.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Laptops")

    def test_category_children(self):
        response = self.client.get(f"/api/categories/{self.parent.slug}/")
        self.assertEqual(len(response.data["children"]), 1)
        self.assertEqual(response.data["children"][0]["name"], "Gaming Laptops")


class ProductFilterSearchTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Laptops", slug="laptops")
        self.brand = Brand.objects.create(name="ASUS", slug="asus")
        self.ram_attr = ProductAttribute.objects.create(name="RAM", unit="GB")

        self.p1 = Product.objects.create(
            title="ASUS ROG Strix G16",
            category=self.category,
            brand=self.brand,
            description="Gaming laptop with RTX 4070",
            base_price=45000000,
            sku="ASUS-ROG-001",
            status="active",
            is_featured=True,
        )
        self.p2 = Product.objects.create(
            title="ASUS VivoBook 15",
            category=self.category,
            brand=self.brand,
            description="Thin and light office laptop",
            base_price=22000000,
            sku="ASUS-VIV-002",
            status="active",
        )
        self.p3 = Product.objects.create(
            title="Logitech Mouse",
            category=self.category,
            base_price=1500000,
            sku="LOGI-M-001",
            status="active",
        )
        ProductAttributeValue.objects.create(
            product=self.p1, attribute=self.ram_attr, value="16GB"
        )
        ProductAttributeValue.objects.create(
            product=self.p2, attribute=self.ram_attr, value="8GB"
        )

    def test_filter_by_brand(self):
        response = self.client.get(f"/api/products/?brand={self.brand.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_category(self):
        response = self.client.get(f"/api/products/?category={self.category.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_filter_by_price_range(self):
        response = self.client.get(
            "/api/products/?min_price=20000000&max_price=50000000"
        )
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_min_price_only(self):
        response = self.client.get("/api/products/?min_price=30000000")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "ASUS ROG Strix G16")

    def test_search_by_title(self):
        response = self.client.get("/api/products/?search=ROG")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "ASUS ROG Strix G16")

    def test_search_by_description(self):
        response = self.client.get("/api/products/?search=office")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "ASUS VivoBook 15")

    def test_search_no_results(self):
        response = self.client.get("/api/products/?search=nonexistent")
        self.assertEqual(response.data["count"], 0)

    def test_ordering_by_price_asc(self):
        response = self.client.get("/api/products/?ordering=price")
        titles = [p["title"] for p in response.data["results"]]
        self.assertEqual(titles, ["Logitech Mouse", "ASUS VivoBook 15", "ASUS ROG Strix G16"])

    def test_ordering_by_price_desc(self):
        response = self.client.get("/api/products/?ordering=-price")
        titles = [p["title"] for p in response.data["results"]]
        self.assertEqual(titles[0], "ASUS ROG Strix G16")

    def test_filter_by_featured(self):
        response = self.client.get("/api/products/?featured=true")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "ASUS ROG Strix G16")

    def test_filter_by_attribute(self):
        response = self.client.get(f"/api/products/?attr_{self.ram_attr.id}=16GB")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "ASUS ROG Strix G16")

    def test_pagination_default_20(self):
        """Verify default page size is 20."""
        for i in range(25):
            Product.objects.create(
                title=f"Product {i}",
                category=self.category,
                base_price=1000000,
                sku=f"PROD-{i:03d}",
                status="active",
            )
        response = self.client.get("/api/products/")
        self.assertEqual(len(response.data["results"]), 20)
        self.assertEqual(response.data["count"], 28)

    def test_product_detail_includes_images_and_attributes(self):
        response = self.client.get(f"/api/products/{self.p1.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("images", response.data)
        self.assertIn("attribute_values", response.data)
        self.assertIn("variants", response.data)
        self.assertEqual(len(response.data["attribute_values"]), 1)

    def test_list_shows_summary_not_detail(self):
        """List serializer should not include description."""
        response = self.client.get("/api/products/")
        first = response.data["results"][0]
        self.assertNotIn("description", first)
        self.assertNotIn("attribute_values", first)
        self.assertIn("category_name", first)
        self.assertIn("brand_name", first)

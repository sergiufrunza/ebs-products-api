from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Category, Price, Product
from .utils.pricing import resolve_overlapping_prices


class PricingTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(name="Test Product", category=self.category)

    def assertPrice(self, price, start, end, value):
        self.assertEqual(price.start_date, start)
        self.assertEqual(price.end_date, end)
        self.assertEqual(price.price, value)

    def test_case_full_overwrite_same_price(self):
        """Case: New infinite interval fully covers existing infinite with same price"""
        Price.objects.create(product=self.product, price=15, start_date=date(2025, 7, 3), end_date=None)
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 1),
            "end_date": None,
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 7, 1), None, 15)

    def test_case_full_overwrite_infinite_over_infinite(self):
        """Case 1: New interval fully covers the old one - old end infinite new end infinite"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 7, 3), end_date=None)
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 1),
            "end_date": None,
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)
        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 7, 1), None, 15)

    def test_case_full_overwrite_infinite_over_finite(self):
        """Case 1: New interval fully covers the old one - old end finite, new end infinite"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 7, 9), end_date=date(2025, 7, 28))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 1),
            "end_date": None,
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 7, 1), None, 15)

    def test_case_full_overwrite_finite_over_finite(self):
        """Case 1: New interval fully covers the old one - both finite"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 7, 9), end_date=date(2025, 7, 28))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 1),
            "end_date": date(2025, 8, 20),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 7, 1), date(2025, 8, 20), 15)

    def test_case_inside_existing(self):
        """Case 2: New interval is completely inside an existing one"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=date(2025, 6, 30))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 10),
            "end_date": date(2025, 6, 20),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 3)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 9), 10)
        self.assertPrice(prices[1], date(2025, 6, 10), date(2025, 6, 20), 15)
        self.assertPrice(prices[2], date(2025, 6, 21), date(2025, 6, 30), 10)

    def test_case_inside_existing_same_price(self):
        """Case: New interval is completely inside an existing one with same price"""
        Price.objects.create(product=self.product, price=15, start_date=date(2025, 6, 1), end_date=date(2025, 6, 30))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 10),
            "end_date": date(2025, 6, 20),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        # Ar trebui să nu creeze nimic nou, dar testăm ca fallback
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 30), 15)

    def test_case_overlap_start(self):
        """Case 3: New interval overlaps only the start of old one"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 5), end_date=date(2025, 6, 30))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 1),
            "end_date": date(2025, 6, 10),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 2)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 10), 15)
        self.assertPrice(prices[1], date(2025, 6, 11), date(2025, 6, 30), 10)

    def test_case_overlap_start_same_price(self):
        """Case: New interval overlaps start of old one, same price"""
        Price.objects.create(product=self.product, price=15, start_date=date(2025, 6, 5), end_date=date(2025, 6, 30))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 1),
            "end_date": date(2025, 6, 10),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 30), 15)

    def test_case_overlap_end(self):
        """Case 4: New interval overlaps only the end of old one"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=date(2025, 6, 20))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 15),
            "end_date": date(2025, 6, 30),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 2)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 14), 10)
        self.assertPrice(prices[1], date(2025, 6, 15), date(2025, 6, 30), 15)

    def test_case_overlap_end_same_price(self):
        """Case: New interval overlaps end of old one, same price"""
        Price.objects.create(product=self.product, price=15, start_date=date(2025, 6, 1), end_date=date(2025, 6, 20))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 15),
            "end_date": date(2025, 6, 30),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 30), 15)

    def test_case_new_wraps_existing(self):
        """Case 5: New interval wraps entirely around old one"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 10), end_date=date(2025, 6, 20))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 5),
            "end_date": date(2025, 6, 25),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 6, 5), date(2025, 6, 25), 15)

    def test_case_touching(self):
        """Case 6: New interval touches the old one (start = old_end + 1)"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=date(2025, 6, 10))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 11),
            "end_date": date(2025, 6, 20),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 2)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 10), 10)
        self.assertPrice(prices[1], date(2025, 6, 11), date(2025, 6, 20), 15)

    def test_case_exact_match(self):
        """Case 7: New interval is exactly equal to the old one"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=date(2025, 6, 15))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 1),
            "end_date": date(2025, 6, 15),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 15), 15)

    def test_case_same_start_new_infinite(self):
        """Case 8: Both intervals start at same time, new one is infinite"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=date(2025, 6, 15))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 1),
            "end_date": None,
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 6, 1), None, 15)

    def test_case_infinite_existing_partial_new(self):
        """Case 9: Old is infinite, new is inside"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=None)
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 10),
            "end_date": date(2025, 6, 20),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 3)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 9), 10)
        self.assertPrice(prices[1], date(2025, 6, 10), date(2025, 6, 20), 15)
        self.assertPrice(prices[2], date(2025, 6, 21), None, 10)

    def test_case_new_before_infinite(self):
        """Case 20: New is before old infinite interval (no overlap)"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 15), end_date=None)
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 1),
            "end_date": date(2025, 6, 10),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 2)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 10), 15)
        self.assertPrice(prices[1], date(2025, 6, 15), None, 10)

    def test_case_full_overwrite_multiple(self):
        """Case 12: New interval fully covers multiple old intervals"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 7, 1), end_date=date(2025, 7, 10))
        Price.objects.create(product=self.product, price=20, start_date=date(2025, 7, 11), end_date=date(2025, 7, 20))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 1),
            "end_date": date(2025, 7, 31),
            "price": 30,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 7, 1), date(2025, 7, 31), 30)

    def test_case_partial_overlap_two_intervals(self):
        """Case 12: New interval overlaps start of one and end of another"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 7, 1), end_date=date(2025, 7, 10))
        Price.objects.create(product=self.product, price=20, start_date=date(2025, 7, 20), end_date=date(2025, 7, 30))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 5),
            "end_date": date(2025, 7, 25),
            "price": 30,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 3)
        self.assertPrice(prices[0], date(2025, 7, 1), date(2025, 7, 4), 10)
        self.assertPrice(prices[1], date(2025, 7, 5), date(2025, 7, 25), 30)
        self.assertPrice(prices[2], date(2025, 7, 26), date(2025, 7, 30), 20)

    def test_case_intervals_touching_each_other(self):
        """Case 13: Two old intervals touch exactly; new overlaps both slightly"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 7, 1), end_date=date(2025, 7, 10))
        Price.objects.create(product=self.product, price=20, start_date=date(2025, 7, 11), end_date=date(2025, 7, 20))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 10),
            "end_date": date(2025, 7, 11),
            "price": 30,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 3)
        self.assertPrice(prices[0], date(2025, 7, 1), date(2025, 7, 9), 10)
        self.assertPrice(prices[1], date(2025, 7, 10), date(2025, 7, 11), 30)
        self.assertPrice(prices[2], date(2025, 7, 12), date(2025, 7, 20), 20)

    def test_case_split_open_ended_by_finite(self):
        """Case 14: New interval is in middle of infinite old"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=None)
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 7, 1),
            "end_date": date(2025, 7, 10),
            "price": 20,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 3)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 30), 10)
        self.assertPrice(prices[1], date(2025, 7, 1), date(2025, 7, 10), 20)
        self.assertPrice(prices[2], date(2025, 7, 11), None, 10)

    def test_case_duplicate_multiple_segments(self):
        """Case 15: New interval exactly duplicates two old ones"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 1), end_date=date(2025, 6, 10))
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 6, 11), end_date=date(2025, 6, 20))
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 1),
            "end_date": date(2025, 6, 20),
            "price": 15,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product)
        self.assertEqual(prices.count(), 1)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 20), 15)

    def test_case_new_completely_before_infinite(self):
        """Case 16: New interval is completely before old infinite interval"""
        Price.objects.create(product=self.product, price=10, start_date=date(2025, 7, 15), end_date=None)
        validated_data = {
            "product": self.product,
            "start_date": date(2025, 6, 1),
            "end_date": date(2025, 6, 30),
            "price": 20,
        }
        new_price = resolve_overlapping_prices(validated_data)
        Price.objects.create(**new_price)

        prices = Price.objects.filter(product=self.product).order_by("start_date")
        self.assertEqual(prices.count(), 2)
        self.assertPrice(prices[0], date(2025, 6, 1), date(2025, 6, 30), 20)
        self.assertPrice(prices[1], date(2025, 7, 15), None, 10)


class AverageByCategoryTestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product1 = Product.objects.create(name="Phone", category=self.category, sku="PH1")
        self.product2 = Product.objects.create(name="Tablet", category=self.category, sku="TB1")

        Price.objects.create(
            product=self.product1, price=Decimal("100.00"), start_date="2024-01-01", end_date="2024-03-01"
        )
        Price.objects.create(
            product=self.product2, price=Decimal("200.00"), start_date="2024-02-01", end_date="2024-04-01"
        )

    def test_average_price_by_category(self):
        url = reverse("price-average-by-category")
        response = self.client.get(
            url, {"category": "Electronics", "start_date": "2024-01-01", "end_date": "2024-04-01"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("average_price", response.data)
        self.assertEqual(round(Decimal(response.data["average_price"]), 2), Decimal("150.00"))


class AverageByProductTestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Appliances")
        self.product = Product.objects.create(name="Fridge", category=self.category, sku="FR1")
        Price.objects.create(
            product=self.product, price=Decimal("300.00"), start_date="2025-06-01", end_date="2025-06-10"
        )
        Price.objects.create(
            product=self.product, price=Decimal("400.00"), start_date="2025-06-11", end_date="2025-06-20"
        )

    def test_product_average_price_by_week(self):
        url = reverse("product-average-price", args=[self.product.id])
        response = self.client.get(url, {"start_date": "2025-06-01", "end_date": "2025-06-30", "group_by": "week"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 2)
        for entry in response.data:
            self.assertIn("period", entry)
            self.assertIn("average_price", entry)

    def test_product_average_price_by_month(self):
        url = reverse("product-average-price", args=[self.product.id])
        response = self.client.get(url, {"start_date": "2025-06-01", "end_date": "2025-06-30", "group_by": "month"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        for entry in response.data:
            self.assertIn("period", entry)
            self.assertIn("average_price", entry)

    def test_average_price_invalid_group_by(self):
        url = reverse("product-average-price", args=[self.product.id])
        response = self.client.get(
            url, {"start_date": "2025-06-01", "end_date": "2025-06-30", "group_by": "daily"}  # invalid
        )
        self.assertEqual(response.status_code, 400)

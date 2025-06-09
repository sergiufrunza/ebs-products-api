from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)

    def __str__(self):
        return f"{self.name}"


class Product(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.sku}"


class Price(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="prices", db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.product.name} - {self.price} ({self.start_date} - {self.end_date})"


class PriceChangeHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_histories", db_index=True)
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.changed_at}"

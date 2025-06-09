from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Category,
    Price,
    Product,
)
from .utils.pricing import resolve_overlapping_prices


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="name", queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = "__all__"


class PriceForCategorySerializer(serializers.Serializer):
    category_id = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00"), coerce_to_string=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False)

    def validate(self, data):
        start_date = data["start_date"]
        end_date = data.get("end_date")

        if end_date and end_date < start_date:
            raise serializers.ValidationError({"start_date": ["Start date must be before end date."]})

        if not Category.objects.filter(id=data["category_id"]).exists():
            raise serializers.ValidationError({"category_id": ["Category does not exist."]})

        return data

    def create_prices_for_category(self):
        validated_data = self.validated_data
        category_id = validated_data["category_id"]
        products = Product.objects.filter(category=category_id)
        if not products.exists():
            raise ValidationError({"category": ["No products found in this category."]})
        created_prices = []
        for product in products:
            price_data = {
                "product": product,
                "price": validated_data["price"],
                "start_date": validated_data["start_date"],
                "end_date": validated_data.get("end_date"),
            }
            resolved_data = resolve_overlapping_prices(price_data)
            created_prices.append(Price.objects.create(**resolved_data))
        return created_prices


class PriceSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00"), coerce_to_string=False)

    class Meta:
        model = Price
        fields = ["id", "product", "price", "start_date", "end_date"]

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if end_date and end_date < start_date:
            raise serializers.ValidationError({"start_date": ["Start date must be before end date."]})

        return data

    def create(self, validated_data):
        new_price = resolve_overlapping_prices(validated_data)
        return super().create(new_price)


class AveragePriceByCategoryInputSerializer(serializers.Serializer):
    category = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError({"start_date": ["Start date must be before end date."]})
        return data


class AveragePriceByProductInputSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    group_by = serializers.ChoiceField(choices=["week", "month"])

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise serializers.ValidationError({"start_date": ["Start date must be before end date."]})
        return data

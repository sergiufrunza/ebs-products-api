from decimal import Decimal

from rest_framework import serializers

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


class PriceSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.00"), coerce_to_string=False)

    class Meta:
        model = Price
        fields = ["id", "product", "price", "start_date", "end_date"]

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if end_date and end_date < start_date:
            raise serializers.ValidationError("End date must be after or equal to start date.")

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

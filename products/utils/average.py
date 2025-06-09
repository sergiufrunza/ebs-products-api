from decimal import Decimal

from django.db.models import Avg, Q
from django.db.models.functions import TruncMonth, TruncWeek
from rest_framework import status
from rest_framework.response import Response

from products.models import Category, Price


def get_average_by_category(category_name, start_date, end_date):
    try:
        category = Category.objects.get(name=category_name)
    except Category.DoesNotExist:
        return Response({"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND)

    prices = Price.objects.filter(
        Q(start_date__lte=end_date),
        Q(end_date__gte=start_date) | Q(end_date__isnull=True),
        product__category=category,
    )

    average_price = prices.aggregate(avg_price=Avg("price"))["avg_price"]
    return Response(
        {
            "category": category.name,
            "start_date": start_date,
            "end_date": end_date,
            "average_price": round(average_price or Decimal("0.00"), 2),
        }
    )


def get_average_by_product(product, start_date, end_date, group_by):
    prices = Price.objects.filter(
        Q(start_date__lte=end_date),
        Q(end_date__gte=start_date) | Q(end_date__isnull=True),
        product=product,
    )
    if group_by == "week":
        prices = prices.annotate(period=TruncWeek("start_date"))
    else:
        prices = prices.annotate(period=TruncMonth("start_date"))
    grouped = prices.values("period").annotate(avg_price=Avg("price")).order_by("period")
    return Response(
        [{"period": entry["period"], "average_price": round(entry["avg_price"] or 0, 2)} for entry in grouped]
    )

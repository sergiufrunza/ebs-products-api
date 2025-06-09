from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.db.models import Q, QuerySet

from products.models import (
    Price,
    Product,
)


def get_overlapping_prices(
    product: Product,
    new_start: date,
    new_end: Optional[date],
) -> QuerySet[Price]:
    prices = Price.objects.filter(product=product)

    if new_end is None:
        return (
            prices.filter(Q(end_date__isnull=True) | Q(end_date__gte=new_start))
            .filter(Q(start_date__lte=new_start) | Q(start_date__gte=new_start))
            .order_by("end_date")
        )
    else:
        return prices.filter(
            Q(start_date__lte=new_end) & (Q(end_date__gte=new_start) | Q(end_date__isnull=True))
        ).order_by("end_date")


def resolve_overlapping_prices(validated_data: dict) -> dict:
    product = validated_data["product"]
    new_start = validated_data["start_date"]
    new_end = validated_data.get("end_date")
    new_price = validated_data["price"]

    overlapping_prices = get_overlapping_prices(product, new_start, new_end)

    for price in overlapping_prices:
        old_start, old_end, old_price = price.start_date, price.end_date, price.price
        price.delete()

        if is_fully_overwritten(new_start, new_end, old_start, old_end):
            continue

        if is_fully_inside(old_start, old_end, new_start, new_end):
            if old_price == new_price:
                validated_data["start_date"] = old_start
                validated_data["end_date"] = old_end
            else:
                create_segment(product, old_price, old_start, new_start - timedelta(days=1))
                if new_end:
                    create_segment(product, old_price, new_end + timedelta(days=1), old_end)
            continue

        if is_overlaps_start(new_start, new_end, old_start, old_end):
            if old_price == new_price:
                validated_data["start_date"] = min(new_start, old_start)
                validated_data["end_date"] = old_end
            else:
                create_segment(product, old_price, new_end + timedelta(days=1), old_end)
            continue

        if is_overlaps_end(new_start, new_end, old_start, old_end):
            if old_price == new_price:
                validated_data["start_date"] = old_start
                validated_data["end_date"] = max(new_end, old_end) if new_end else old_end
            else:
                create_segment(product, old_price, old_start, new_start - timedelta(days=1))

    return validated_data


def create_segment(product, price: Decimal, start: date, end: Optional[date]) -> None:
    if end is None or start <= end:
        Price.objects.create(
            product=product,
            price=price,
            start_date=start,
            end_date=end,
        )


def is_fully_overwritten(new_start: date, new_end: Optional[date], old_start: date, old_end: Optional[date]) -> bool:
    return new_start <= old_start and (new_end is None or old_end is None or new_end >= old_end)


def is_fully_inside(old_start: date, old_end: Optional[date], new_start: date, new_end: Optional[date]) -> bool:
    return old_start < new_start and (old_end is None or (new_end is not None and new_end < old_end))


def is_overlaps_start(new_start: date, new_end: Optional[date], old_start: date, old_end: Optional[date]) -> bool:
    return new_start <= old_start and new_end is not None and old_end is not None and new_end < old_end


def is_overlaps_end(new_start: date, new_end: Optional[date], old_start: date, old_end: Optional[date]) -> bool:
    return old_start < new_start and (old_end is None or (new_end is not None and new_end >= old_end))

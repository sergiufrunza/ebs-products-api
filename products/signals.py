from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Price, PriceChangeHistory


@receiver(pre_delete, sender=Price)
def create_price_history_on_delete(sender, instance, **kwargs):
    PriceChangeHistory.objects.create(
        product=instance.product, old_price=instance.price, start_date=instance.start_date, end_date=instance.end_date
    )

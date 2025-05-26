from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from inventory.models import StockInModel


@receiver(post_save, sender=StockInModel)
def stock_inventory(sender, instance, created, **kwargs):
    if created:
        stock = instance
        product = stock.product

        product.quantity += stock.quantity_added
        product.save()



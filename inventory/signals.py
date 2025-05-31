from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from inventory.models import StockInModel, ProductModel, PriceHistoryModel, StockOutModel


@receiver(post_save, sender=StockInModel)
def stock_inventory(sender, instance, created, **kwargs):
    if created:
        stock = instance
        product = stock.product

        product.quantity += stock.quantity_added
        product.save()


@receiver(pre_save, sender=ProductModel)
def record_price_change(sender, instance, **kwargs):
    """
    Records a price change in PriceHistoryModel when a ProductModel instance is saved
    and its price field has been modified.
    """
    if instance.pk: # Check if the instance already exists (i.e., it's an update, not a creation)
        try:
            # Get the old instance from the database
            old_instance = sender.objects.get(pk=instance.pk)
            # Compare the old price with the new price
            if old_instance.price != instance.price:
                # If prices are different, create a PriceHistoryModel object
                PriceHistoryModel.objects.create(
                    product=instance,
                    old_price=old_instance.price,
                    new_price=instance.price
                )
                print(f"Price change recorded for {instance.name}: {old_instance.price} -> {instance.price}")
        except sender.DoesNotExist:
            # This can happen if the object is new but has a PK assigned before save
            # Or if there's a race condition. For simplicity, we'll ignore for now.
            pass
        except Exception as e:
            # Log any other exceptions that might occur
            print(f"Error recording price change for {instance.name}: {e}")


@receiver(post_save, sender=StockOutModel)
def update_product_quantity_on_stock_out(sender, instance, created, **kwargs):
    """
    Reduces the associated product's quantity_in_stock when a StockOutModel record is created or updated.
    Adjusts based on the difference if the quantity_removed is changed.
    """
    # Ensure the related stock and product objects exist
    if instance.stock and instance.stock.product:
        stock = instance.stock
        product = stock.product

        if created:
            # If it's a new StockOut record, simply subtract the quantity removed
            product.quantity -= instance.quantity_removed
            stock.quantity_left -= instance.quantity_removed
            stock.quantity_stocked_out += instance.quantity_removed

        # Ensure quantity_in_stock doesn't go below zero if your logic requires it
        if product.quantity < Decimal('0.00'):
            product.quantity = Decimal('0.00')

        if stock.quantity_left <= Decimal('0.00'):
            stock.status = 'finished'

        if stock.quantity_left < Decimal('0.00'):
            stock.quantity_left = Decimal('0.00')

        # Save the updated ProductModel instance, but only update the quantity field
        product.save()
        stock.save()

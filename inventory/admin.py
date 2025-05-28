from django.contrib import admin
from inventory.models import StockInModel,SaleModel


admin.site.register(StockInModel)
admin.site.register(SaleModel)
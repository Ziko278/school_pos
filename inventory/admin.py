from django.contrib import admin
from inventory.models import StockInModel,SaleModel, StockOutModel


admin.site.register(StockInModel)
admin.site.register(SaleModel)
admin.site.register(StockOutModel)
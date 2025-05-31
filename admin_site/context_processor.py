from django.db.models import F

from admin_site.models import SchoolInfoModel, SchoolSettingModel
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.shortcuts import redirect
from inventory.models import ProductModel
from user_site.models import User


def school_info(request):
    info = SchoolInfoModel.objects.first()
    low_stock = ProductModel.objects.filter(quantity__lte=F('reorder_level')).order_by('name')
    return {
        'school_info': info,
        'academic_info': SchoolSettingModel.objects.first(),
        'low_stock_list': low_stock,
        'low_stock': low_stock.count()
    }

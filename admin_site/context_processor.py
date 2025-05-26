from admin_site.models import SchoolInfoModel, SchoolSettingModel
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.shortcuts import redirect


def school_info(request):
    info = SchoolInfoModel.objects.first()

    return {
        'school_info': info,
        'academic_info': SchoolSettingModel.objects.first()
    }

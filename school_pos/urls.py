from django.contrib import admin, messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static

from user_site.models import UserProfileModel


def home_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect(reverse('admin_dashboard'))
        try:
            user_role = UserProfileModel.objects.get(user=request.user)
        except UserProfileModel.DoesNotExist:
            messages.error(request, 'Unknown Identity, Access Denied')
            logout(request)
            return redirect(reverse('login'))

        if user_role.staff:
            return redirect(reverse('admin_dashboard'))

        return redirect(reverse('student_dashboard'))
    else:
        return redirect(reverse('login'))


urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', include('admin_site.urls')),
    path('admin/student/', include('student.urls')),
    path('admin/inventory/', include('inventory.urls')),
    path('student/', include('student_site.urls')),
    path('user/', include('user_site.urls')),
    path('admin/human_resource/', include('human_resource.urls')),
    path('django-admin/', admin.site.urls),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

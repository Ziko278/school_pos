from django.urls import path, include
from user_site.views import *

urlpatterns = [

    path('sign-in', user_sign_in_view, name='login'),
    path('sign-out', user_sign_out_view, name='logout'),

]

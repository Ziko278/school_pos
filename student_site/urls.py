from django.urls import path
from student_site.views import *


urlpatterns = [
    path('', StudentDashboardView.as_view(), name='student_dashboard'),
    path('order-placement', student_place_order_view, name='student_place_order'),
    path('order/index', view_student_orders, name='student_order'),
    path('order/<int:pk>/detail', student_order_detail, name='student_order_detail'),

]


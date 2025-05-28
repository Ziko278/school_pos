from django.urls import path
from parent_site.views import *


urlpatterns = [
    path('', ParentDashboardView.as_view(), name='parent_dashboard'),
    path('payment/select-method', payment_method_select_view, name='payment_method_select'),
    path('payment/<int:amount>/<str:method>', student_payment_view, name='student_payment'),
    path('payment/index', student_payment_index_view, name='student_payment_index'),
    path('order/index', view_student_orders, name='parent_order'),
    path('order/<int:pk>/detail', student_order_detail, name='parent_order_detail'),
    path('payment/paystack', verfiy_paystack_payment, name='parent_verfiy_paystack_payment'),

]


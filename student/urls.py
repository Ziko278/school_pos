from django.urls import path
from student.views import *

urlpatterns = [
    path('register', StudentCreateView.as_view(), name='student_create'),
    path('index', StudentListView.as_view(), name='student_index'),
    path('class/index', class_student_list_view, name='student_class_index'),
    path('<int:pk>/detail', StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/edit', StudentUpdateView.as_view(), name='student_edit'),
    path('login-detail', student_login_detail_view, name='student_login_detail'),
    path('<int:pk>/delete', StudentDeleteView.as_view(), name='student_delete'),

    path('deposit/select-student', DepositPaymentSelectStudentView.as_view(), name='deposit_select_student'),
    path('deposit/get-class-student', deposit_get_class_students, name='deposit_get_class_students'),
    path('deposit/get-student-by-reg-number', deposit_get_class_students_by_reg_number,
         name='deposit_get_class_students_by_reg_number'),
    path('deposit/payment/index', deposit_payment_list_view, name='deposit_index'),
    path('deposit/payment/pending/index', pending_deposit_payment_list_view, name='pending_deposit_index'),
    path('deposit/<int:student_pk>/create', deposit_create_view, name='deposit_create'),
    path('deposit/<int:payment_id>/confirm/', confirm_payment_view, name='confirm_payment'),
    path('deposit/<int:payment_id>/cancel/', decline_payment_view, name='decline_payment'),

]


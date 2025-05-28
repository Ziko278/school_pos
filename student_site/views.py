from datetime import date
from decimal import Decimal

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from num2words import num2words

from admin_site.models import SchoolSettingModel
from inventory.models import SaleModel, SaleItemModel, ProductModel, StockInModel
from student.forms import StudentFundingForm
from student.models import StudentModel, StudentFundingModel, StudentWalletModel


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'student_site/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.profile.student  # Get the logged-in student's instance
        context['student'] = student

        today = date.today()  # Get today's date

        # --- 1. Academic Info ---
        # Assuming SchoolSettingModel holds current academic session and term
        academic_info = SchoolSettingModel.objects.first()
        context['academic_info'] = academic_info

        # --- 2. Products Bought Today (by the student) ---
        # Now using SaleItemModel to count actual items sold in completed sales
        total_products = SaleItemModel.objects.filter(
            sale__student=student,
            sale__sale_date=today,
            sale__status='completed'
        ).aggregate(total_items=Sum('quantity'))['total_items'] or 0
        context['total_products'] = total_products

        # --- 3. Amount Spent Today (by the student) ---
        # Now using SaleModel for total_amount in completed sales
        total_amount_spent_today = SaleModel.objects.filter(
            student=student,
            sale_date=today,
            status='completed'
        ).aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0.00
        context['total_amount_spent_today'] = total_amount_spent_today

        # --- 4. Total Students in School ---
        # This replaces the 'Staff' card as it's more relevant for a student dashboard
        total_students_in_school = StudentModel.objects.count()
        context['total_students_in_school'] = total_students_in_school

        # --- 5. Amount Spent Current Term (by the student) ---
        # Now using SaleModel for total_amount in completed sales for the current term
        total_amount_spent_current_term = 0.00
        if academic_info and academic_info.term:
            total_amount_spent_current_term = SaleModel.objects.filter(
                student=student,
                term=academic_info.term,
                session=academic_info.session,
                status='completed'
            ).aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0.00
        context['total_amount_spent_current_term'] = total_amount_spent_current_term

        # --- 6. Total Deposits (by the student, only confirmed ones) ---
        # Using StudentFundingModel for total_amount of confirmed deposits
        total_deposits = StudentFundingModel.objects.filter(
            student=student,
            status='confirmed' # Only sum confirmed deposits
        ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.00
        context['total_deposits'] = total_deposits

        return context


@transaction.atomic
def student_place_order_view(request):
    student = request.user.profile.student
    if request.method == 'GET':
        settings_obj = SchoolSettingModel.objects.last()
        context = {
            'settings': settings_obj,
            'products': ProductModel.objects.all(),
            'student': student
        }
        return render(request, 'student_site/sale/place_order.html', context)


    wallet, _ = StudentWalletModel.objects.get_or_create(student=student)

    idx = 0
    items = []
    total_amount = Decimal('0.00')
    total_items  = 0
    while True:
        pid = request.POST.get(f'products[{idx}][product_id]')
        qty = request.POST.get(f'products[{idx}][quantity]')
        if not pid or not qty:
            break
        product    = get_object_or_404(ProductModel, pk=pid)
        quantity   = int(qty)
        unit_price = product.price
        line_total = unit_price * quantity

        items.append((product, quantity, unit_price))
        total_amount += line_total
        total_items  += quantity
        idx += 1

    sale = SaleModel.objects.create(
        student=student,
        total_amount=total_amount,
        total_items=total_items,
        status='pending'
    )

    for product, qty, unit_price in items:
        SaleItemModel.objects.create(
            sale=sale,
            product=product,
            quantity=qty,
            unit_price=unit_price,
            cost_price=Decimal('0.00'),
            profit=Decimal('0.00'),
            subtotal=unit_price * qty
        )

    messages.success(request, 'Order placed successfully. Kindly go and collect your Order.')
    return redirect(reverse('student_order'))


def view_student_orders(request):
    # (You can add filtering, pagination, etc.)
    student = request.user.profile.student
    school_setting = SchoolSettingModel.objects.first()
    orders = SaleModel.objects.filter(student=student, term=school_setting.term, session=school_setting.session)
    return render(request, 'student_site/sale/index.html', {
        'orders': orders,
        'student': student
    })


def student_order_detail(request, pk):
    sale = get_object_or_404(SaleModel, pk=pk)
    student = request.user.profile.student
    if student != sale.student:
        messages.warning(request, 'Access Denied')
        return redirect(reverse('student_sale_index'))
    items = sale.saleitemmodel_set.select_related('product')
    # Compute total profit here
    return render(request, 'student_site/sale/detail.html', {
        'sale': sale,
        'items': items,
    })

from datetime import date

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Sum
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
from inventory.models import SaleModel, SaleItemModel
from student.forms import StudentFundingForm
from student.models import StudentModel, StudentFundingModel, StudentWalletModel


class ParentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'parent_site/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.profile.parent  # Get the logged-in student's instance
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
        # This replaces the 'Staff' card as it's more relevant for a parent dashboard
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



def payment_method_select_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        method = request.POST.get('mode')

        try:
            amount = int(amount_str)
            if amount <= 0:
                messages.error(request, 'Amount must be a positive number.')
                return redirect(reverse('student_payment_select'))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount entered.')
            return redirect(reverse('student_payment_select'))

        # Basic method validation (you might have a predefined list of valid methods)
        valid_methods = ['online', 'offline'] # Example valid methods
        if method not in valid_methods:
            messages.error(request, 'Invalid payment method selected.')
            return redirect(reverse('student_payment_select'))

        return redirect(reverse('student_payment', kwargs={'amount': amount, 'method': method}))
    context = {
        'student': request.user.profile.parent
    }
    return render(request, 'parent_site/payment/select.html', context)


def student_payment_view(request, amount, method):
    if request.method == 'POST':
        form = StudentFundingForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save()
            messages.success(request, 'Your Payment has been received, Your Child wallet will be credited once confirmed')
            return redirect(reverse('student_payment_index'))
    else:
        form = StudentFundingForm
    try:
        amount = int(amount)
    except ValueError:
        messages.error(request, 'Invalid Amount Entered')
        return redirect(reverse('payment_method_select'))
    school_setting = SchoolSettingModel.objects.first()
    if method == 'offline' and (not school_setting.account_number or not school_setting.bank):
        messages.error(request, 'Offline Payment Not Currently Supported, Try another Method')
        return redirect(reverse('payment_method_select'))
    amount_in_word = num2words(amount)

    context = {
        'method': method,
        'amount': amount,
        'amount_in_word': amount_in_word,
        'student': request.user.profile.parent,
        'school_setting': school_setting,
        'form': form,
        'secret_key': settings.PAYSTACK_PUBLIC_KEY,
        'callback_url': reverse('parent_verfiy_paystack_payment')
    }
    return render(request, 'parent_site/payment/pay.html', context)


@login_required
@csrf_exempt
def verfiy_paystack_payment(request):
    if 'reference' in request.GET:
        reference = request.GET['reference']
        url = "https://api.paystack.co/transaction/verify/{}".format(reference)

        secret_key = settings.PAYSTACK_SECRET_KEY

        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }
        response = requests.request("GET", url, headers=headers)
        response = response.json()

        meta_data = response["data"]["metadata"]

        if response["status"]:
            payment_exist = StudentFundingModel.objects.filter(reference=reference)
            if payment_exist:
                messages.warning(request, 'Payment already Processed, Thank You')
                return redirect(reverse('student_payment_index'))

            student_id = meta_data["student_id"]
            amount = float(meta_data["amount"]) / 100
            student = StudentModel.objects.get(pk=student_id)
            status = 'confirmed'

            payment = StudentFundingModel.objects.create(student=student, mode='online',
                                                     amount=amount, reference=reference, status=status)
            payment.save()
            if payment.id:
                student_wallet, created = StudentWalletModel.objects.get_or_create(
                    student=student)  # Get or create wallet

                student_wallet.balance += amount

                if student_wallet.debt > 0:
                    if student_wallet.balance > student_wallet.debt:
                        student_wallet.balance -= student_wallet.debt
                        student_wallet.debt = 0
                    else:
                        student_wallet.debt -= student_wallet.balance
                        student_wallet.balance = 0

                student_wallet.save()

                payment.balance = student_wallet.balance - student_wallet.debt
                payment.save()  # Now save the deposit

                messages.success(request, 'N{} Payment Processed Successfully'.format(amount))

            return redirect(reverse('student_payment_index'))
        else:
            if response.data.status == 'failed':
                messages.error(request, 'Payment Processing Failed, Try Later')
            elif response.data.status == 'pending':
                messages.warning(request, 'Payment Processing Pending, Please wait while we try to process the payment')
            else:
                messages.warning(request,
                                 'Payment Status not known. Please if you have been charged, wait a while for it to be resolved')
            return redirect(reverse('student_payment_index'))
    else:
        messages.warning(request, 'Invalid Transaction Link')
        return redirect(reverse('student_payment_index'))


def student_payment_index_view(request):
    student = request.user.profile.parent
    school_setting = SchoolSettingModel.objects.first()
    payment_list = StudentFundingModel.objects.filter(student=student, term=school_setting.term, session=school_setting.session)
    context = {
        'session': school_setting.session,
        'term': school_setting.term,
        'payment_list': payment_list,
        'student': student,
    }

    return render(request, 'parent_site/payment/index.html', context)


def view_student_orders(request):
    # (You can add filtering, pagination, etc.)
    student = request.user.profile.parent
    school_setting = SchoolSettingModel.objects.first()
    orders = SaleModel.objects.filter(student=student, term=school_setting.term, session=school_setting.session)
    return render(request, 'parent_site/sale/index.html', {
        'orders': orders,
        'student': student
    })


def student_order_detail(request, pk):
    sale = get_object_or_404(SaleModel, pk=pk)
    student = request.user.profile.parent
    if student != sale.student:
        messages.warning(request, 'Access Denied')
        return redirect(reverse('student_sale_index'))
    items = sale.saleitemmodel_set.select_related('product')
    # Compute total profit here
    return render(request, 'parent_site/sale/detail.html', {
        'sale': sale,
        'items': items,
    })

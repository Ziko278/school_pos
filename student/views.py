import io

from django.contrib.messages.views import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import resolve
from django.core import serializers
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from xlsxwriter import Workbook
from django.apps import apps
from student.models import *
from student.forms import *


class StudentCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = StudentModel
    permission_required = 'student.add_studentmodel'
    form_class = StudentForm
    template_name = 'student/student/create.html'
    success_message = 'Student Successfully Registered'

    def get_success_url(self):
        return reverse('student_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['student_setting'] = SchoolSettingModel.objects.filter().first()
        context['class_list'] = ClassesModel.objects.all().order_by('name')

        return context


class StudentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StudentModel
    permission_required = 'student.view_studentmodel'
    fields = '__all__'
    template_name = 'student/student/index.html'
    context_object_name = "student_list"

    def get_queryset(self):
        return StudentModel.objects.filter().exclude(status='graduated').order_by('surname')


def class_student_list_view(request):
    if 'student_class' in request.GET and 'class_section' in request.GET:
        student_class = request.GET.get('student_class')
        class_section = request.GET.get('class_section')
        student_list = StudentModel.objects.filter(student_class__id=student_class, class_section__id=class_section).order_by('surname')
        context = {
            'student_list': student_list,
            'student_class': ClassesModel.objects.get(pk=student_class),
            'class_section': ClassSectionModel.objects.get(pk=class_section),
            'is_class': True
        }
        return render(request, 'student/student/index.html', context)

    class_list = ClassesModel.objects.all().order_by('name')
    context = {
        'class_list': class_list,
    }
    return render(request, 'student/student/select_class.html', context)


class StudentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = StudentModel
    permission_required = 'student.view_studentmodel'
    fields = '__all__'
    template_name = 'student/student/detail.html'
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['student'] = self.object

        return context


class StudentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = StudentModel
    permission_required = 'student.change_studentmodel'
    form_class = StudentForm
    template_name = 'student/student/edit.html'
    success_message = 'Student Information Successfully Updated'

    def get_success_url(self):
        return reverse('student_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super(StudentUpdateView, self).get_form_kwargs()
        # kwargs.update({'division': self.request.session['division']})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.object
        context['student_setting'] = SchoolSettingModel.objects.filter().first()
        context['class_list'] = ClassesModel.objects.all().order_by('name')
        return context


class StudentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = StudentModel
    permission_required = 'student.delete_studentsmodel'
    fields = '__all__'
    template_name = 'student/student/delete.html'
    context_object_name = "student"
    success_message = 'Student Successfully Deleted'

    def get_success_url(self):
        return reverse('student_index')


@login_required
def student_login_detail_view(request):
    if request.method == 'GET':
        student_class = request.GET.get('student_class')
        class_section = request.GET.get('class_section')
        student_list = StudentModel.objects.filter(student_class__id=student_class,
                                                    class_section__id=class_section).order_by('surname')
        context = {
            'student_list': student_list,
            'student_class': ClassesModel.objects.get(pk=student_class),
            'class_section': ClassSectionModel.objects.get(pk=class_section),
        }

        return render(request, 'student/student/login_detail.html', context)
    else:
        student_class = ClassesModel.objects.get(id=request.POST.get('student_class'))
        class_section = ClassSectionModel.objects.get(id=request.POST.get('class_section'))

        student_list = StudentModel.objects.filter(student_class=student_class,
                                                    class_section=class_section).order_by('surname')

        field_list = ['student', 'username', 'password']
        file_name = f"{student_class.__str__()} {class_section.__str__()}-STUDENT-LOGIN-DETAILS"
        if not student_list:
            messages.warning(request, 'No Student Selected')
            return redirect(reverse('student_class_index'))

        output = io.BytesIO()

        workbook = Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        for num in range(len(field_list)):
            field = field_list[num]
            worksheet.write(0, num, field.title())

        for row in range(len(student_list)):
            student = student_list[row]

            for col in range(len(field_list)):
                field = field_list[col]
                if field == 'student':
                    value = student.__str__()
                elif field == 'username':
                    value = student.registration_number
                elif field == 'password':
                    try:
                        value = UserProfileModel.objects.get(student=student).default_password
                    except Exception:
                        value = ''
                else:
                    value = ''
                worksheet.write(row + 1, col, value)
        workbook.close()

        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response['Content-Disposition'] = "attachment; filename=" + file_name + ".xlsx"

        output.close()

        return response


class DepositPaymentSelectStudentView(LoginRequiredMixin, SuccessMessageMixin, TemplateView):
    template_name = 'student/fee_payment/select_student.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_list'] = ClassesModel.objects.all().order_by('name')
        student_list = StudentModel.objects.all()
        context['student_list'] = serializers.serialize("json", student_list)
        return context


def deposit_get_class_students(request):
    class_pk = request.GET.get('class_pk')
    section_pk = request.GET.get('section_pk')

    student_list = StudentModel.objects.filter(student_class=class_pk, class_section=section_pk)
    result = ''
    for student in student_list:
        full_name = "{} {}".format(student.surname.title(), student.last_name.title())
        result += """<li class='list-group-item select_student d-flex justify-content-between align-items-center' student_id='{}'>
        {} </li>""".format(student.id, full_name)
    if result == '':
        result += """<li class='list-group-item  d-flex justify-content-between align-items-center bg-danger text-white'>
        No Student in Selected Class</li>"""
    return HttpResponse(result)


def deposit_get_class_students_by_reg_number(request):
    reg_no = request.GET.get('reg_no')

    student_list = StudentModel.objects.filter(registration_number__contains=reg_no)
    result = ''
    for student in student_list:
        full_name = "{} {}".format(student.surname.title(), student.last_name.title())
        result += """<li class='list-group-item select_student d-flex justify-content-between align-items-center' student_id={}>
        {} </li>""".format(student.id, full_name)
    if result == '':
        result += """<li class='list-group-item d-flex justify-content-between align-items-center bg-danger text-white'>
        No Student in with inputed Registration Number</li>"""
    return HttpResponse(result)


def deposit_payment_list_view(request):
    session_id = request.GET.get('session', None)
    school_setting = SchoolSettingModel.objects.first()
    if not session_id:
        session = school_setting.session
    else:
        session = SessionModel.objects.get(id=session_id)
    session_list = SessionModel.objects.all()
    term = request.GET.get('term', None)
    if not term:
        term = school_setting.term
    fee_payment_list = StudentFundingModel.objects.filter(session=session, term=term).exclude(status='pending').order_by('-id')
    context = {
        'fee_payment_list': fee_payment_list,
        'session': session,
        'term': term,
        'session_list': session_list
    }
    return render(request, 'student/fee_payment/index.html', context)


def pending_deposit_payment_list_view(request):
    session_id = request.GET.get('session', None)
    session = SessionModel.objects.get(id=session_id)
    session_list = SessionModel.objects.all()
    term = request.GET.get('term', None)
    fee_payment_list = StudentFundingModel.objects.filter(session=session, term=term, status='pending').order_by('-id')
    context = {
        'fee_payment_list': fee_payment_list,
        'session': session,
        'term': term,
        'session_list': session_list
    }
    return render(request, 'student/fee_payment/pending.html', context)


def deposit_create_view(request, student_pk):
    student = StudentModel.objects.get(pk=student_pk)
    setting = SchoolSettingModel.objects.first()

    if request.method == 'POST':
        form = StudentFundingForm(request.POST, request.FILES)  # Pass request.FILES for file uploads
        if form.is_valid():
            deposit = form.save(commit=False)  # Don't save yet, we need to set the student
            deposit.student = student  # Associate the funding with the student

            # Set session and term based on school setting if not provided by form
            if not deposit.session:
                deposit.session = setting.session
            if not deposit.term:
                deposit.term = setting.term

            amount = deposit.amount  # Get amount directly from the saved instance
            messages.success(request, f'Deposit of ₦{amount} successful!')

            # Update student wallet
            student_wallet, created = StudentWalletModel.objects.get_or_create(student=student)  # Get or create wallet

            student_wallet.balance += amount

            if student_wallet.debt > 0:
                if student_wallet.balance > student_wallet.debt:
                    student_wallet.balance -= student_wallet.debt
                    student_wallet.debt = 0
                else:
                    student_wallet.debt -= student_wallet.balance
                    student_wallet.balance = 0

            student_wallet.save()

            deposit.balance = student_wallet.balance - student_wallet.debt
            deposit.save()  # Now save the deposit

            return redirect('deposit_create',
                            student_pk=student_pk)  # Redirect to prevent form resubmission on refresh
        else:
            # If form is not valid, messages.error can show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = StudentFundingForm()  # Instantiate an empty form for GET request

    context = {
        'student': student,
        'form': form,
        'payment_list': StudentFundingModel.objects.filter(student=student, term=setting.term,
                                                           session=setting.session).order_by('-created_at'),
        'setting': setting
    }
    return render(request, 'student/fee_payment/create.html', context)


@transaction.atomic
def confirm_payment_view(request, payment_id):
    payment = get_object_or_404(StudentFundingModel, pk=payment_id)
    student = payment.student # Get the student associated with this payment

    if request.method == 'POST':
        # Check if the payment is already confirmed or declined
        if payment.status != 'pending':
            messages.warning(request, f"Payment is already {payment.status.capitalize()}. Cannot confirm.")
            # Redirect to a list of payments or the payment detail page
            return redirect(reverse('pending_deposit_index')) # Replace with your actual URL name

        # Get or create student wallet
        student_wallet, created = StudentWalletModel.objects.get_or_create(student=student)

        # Apply the payment amount to the wallet balance
        # Keeping calculations as float as per original deposit_create_view
        student_wallet.balance += payment.amount

        # Apply debt reduction logic
        if student_wallet.debt > 0:
            if student_wallet.balance > student_wallet.debt:
                student_wallet.balance -= student_wallet.debt
                student_wallet.debt = 0.0 # Use 0.0 for float consistency
            else:
                student_wallet.debt -= student_wallet.balance
                student_wallet.balance = 0.0 # Use 0.0 for float consistency

        student_wallet.save() # Save the updated wallet

        # Update the payment status and its internal balance field
        payment.status = 'confirmed'
        # Replicate the balance update from the original view
        payment.balance = student_wallet.balance - student_wallet.debt
        payment.save() # Save the updated payment record

        messages.success(request, f"Payment of ₦{payment.amount} for {student.surname} {student.last_name} confirmed successfully.")
        return redirect(reverse('deposit_index')) # Replace with your actual URL name

    else:
        # For GET requests to this URL, you might want to display a confirmation prompt
        # or just redirect with a message. Assuming redirect for simplicity.
        messages.info(request, "Please use a POST request to confirm this payment.")
        return redirect(reverse('pending_deposit_index'))  # Replace with your actual URL name


# --- Decline Payment View ---
@transaction.atomic
def decline_payment_view(request, payment_id):
    payment = get_object_or_404(StudentFundingModel, pk=payment_id)
    student = payment.student # Get the student associated with this payment

    if request.method == 'POST':
        # Check if the payment is already confirmed or declined
        if payment.status != 'pending':
            messages.warning(request, f"Payment is already {payment.status.capitalize()}. Cannot decline.")
            # Redirect to a list of payments or the payment detail page
            return redirect(reverse('pending_deposit_index')) # Replace with your actual URL name

        # Update the payment status to 'declined'
        payment.status = 'declined'
        payment.save()

        messages.success(request, f"Payment of ₦{payment.amount} for {student.surname} {student.last_name} has been declined.")
        return redirect(reverse('deposit_index'))  # Replace with your actual URL name
    else:
        # For GET requests to this URL, you might want to display a confirmation prompt
        # or just redirect with a message. Assuming redirect for simplicity.
        messages.info(request, "Method Not Supported.")
        return redirect(reverse('pending_deposit_index'))  # Replace with your actual URL name


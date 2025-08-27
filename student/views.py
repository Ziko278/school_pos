import base64
import io
import math
from datetime import date

from django.utils import timezone
from django.utils.timezone import now
from pytz import timezone as pytz_timezone
from django.contrib.messages.views import messages
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import resolve
from django.core import serializers
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from xlsxwriter import Workbook
from django.apps import apps

from admin_site.models import ActivityLogModel
from inventory.models import SaleModel, SaleItemModel
from student.models import *
from student.forms import *
from student.signals import get_day_ordinal_suffix


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


@login_required
@permission_required("student.view_studentmodel", raise_exception=True)
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
        school_setting = SchoolSettingModel.objects.first()
        today = date.today()
        student = self.object
        context['student'] = student
        context['school_setting'] = school_setting
        context['max_ticket'] = math.floor(student.student_wallet.balance/school_setting.meal_cost)

        context['payment_list'] = StudentFundingModel.objects.filter(student=student, term=school_setting.term,
                                                          session=school_setting.session).order_by('-created_at')
        context['order_list'] = SaleModel.objects.filter(student=student, term=school_setting.term, session=school_setting.session)
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
        if school_setting and school_setting.term:
            total_amount_spent_current_term = SaleModel.objects.filter(
                student=student,
                term=school_setting.term,
                session=school_setting.session,
                status='completed'
            ).aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0.00
        context['total_amount_spent_current_term'] = total_amount_spent_current_term

        # --- 6. Total Deposits (by the student, only confirmed ones) ---
        # Using StudentFundingModel for total_amount of confirmed deposits
        total_deposits = StudentFundingModel.objects.filter(
            student=student,
            status='confirmed'  # Only sum confirmed deposits
        ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0.00
        context['total_deposits'] = total_deposits
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
    permission_required = 'student.delete_studentmodel'
    fields = '__all__'
    template_name = 'student/student/delete.html'
    context_object_name = "student"
    success_message = 'Student Successfully Deleted'

    def get_success_url(self):
        return reverse('student_index')


@login_required
@permission_required("student.view_studentmodel", raise_exception=True)
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


class DepositPaymentSelectStudentView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, TemplateView):
    template_name = 'student/fee_payment/select_student.html'
    permission_required = 'student.add_studentfundingmodel'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_list'] = ClassesModel.objects.all().order_by('name')
        student_list = StudentModel.objects.all()
        context['student_list'] = serializers.serialize("json", student_list)
        return context


@login_required
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


@login_required
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


@login_required
@permission_required("student.view_studentfundingmodel", raise_exception=True)
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


@login_required
@permission_required("student.view_studentfundingmodel", raise_exception=True)
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


@login_required
@permission_required("student.add_studentfundingmodel", raise_exception=True)
def deposit_create_view(request, student_pk):
    student = StudentModel.objects.get(pk=student_pk)
    setting = SchoolSettingModel.objects.first()

    if request.method == 'POST':
        form = StudentFundingForm(request.POST, request.FILES)  # Pass request.FILES for file uploads
        if form.is_valid():
            deposit = form.save(commit=False)  # Don't save yet, we need to set the student
            deposit.student = student  # Associate the funding with the student

            try:
                profile = UserProfileModel.objects.get(user=request.user)
                deposit.created_by = profile.staff
            except Exception:
                pass
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

            target_timezone = pytz_timezone('Africa/Lagos')

            localized_created_at = timezone.localtime(deposit.created_at, timezone=target_timezone)

            formatted_time = localized_created_at.strftime(
                f"%B {localized_created_at.day}{get_day_ordinal_suffix(localized_created_at.day)} %Y %I:%M%p"
            )

            log = f"""
                       <div class='text-white bg-success' style='padding:5px;'>
                       <p class=''>Student Wallet Funding: <a href={reverse('deposit_detail', kwargs={'pk': deposit.id})}><b>₦{amount}</b></a> deposit to wallet of
                       <a href={reverse('student_detail', kwargs={'pk': deposit.student.id})}><b>{deposit.student.__str__().title()}</b></a>
                        by <a href={reverse('staff_detail', kwargs={'pk': deposit.created_by.id})}><b>{deposit.created_by.__str__().title()}</b></a>
                       <br><span style='float:right'>{formatted_time}</span>
                       </p>

                       </div>
                       """

            activity = ActivityLogModel.objects.create(log=log)
            activity.save()

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


@login_required
def deposit_detail_view(request, pk):
    deposit = get_object_or_404(StudentFundingModel, pk=pk)

    # Compute total profit here
    return render(request, 'student/fee_payment/detail.html', {
        'funding': deposit,
    })


@login_required
@permission_required("student.change_studentfundingmodel", raise_exception=True)
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

        # Log wallet confirmation
        from pytz import timezone as pytz_timezone
        localized_created_at = timezone.localtime(now(), timezone=pytz_timezone('Africa/Lagos'))
        formatted_time = localized_created_at.strftime(
            f"%B {localized_created_at.day}{get_day_ordinal_suffix(localized_created_at.day)} %Y %I:%M%p"
        )

        student_url = reverse('student_detail', kwargs={'pk': student.pk})
        payment_url = reverse('deposit_detail', kwargs={'pk': payment.pk})
        staff = UserProfileModel.objects.get(user=request.user).staff
        staff_url = reverse('staff_detail', kwargs={'pk': staff.pk}) if staff else '#'

        log = f"""
        <div class='text-white bg-success p-2' style='border-radius:5px;'>
          <p>
            Payment of <a href="{payment_url}"><b>₦{payment.amount:.2f}</b></a> for
            <a href="{student_url}"><b>{student.__str__().title()}</b></a> was
            <b>confirmed</b> by
            <a href="{staff_url}"><b>{staff.__str__().title()}</b></a>.
            <br>
            <b>Status:</b> Confirmed &nbsp; | &nbsp;
            <b>Wallet Balance:</b> ₦{student_wallet.balance:.2f}
            <span class='float-end'>{now().strftime('%Y-%m-%d %H:%M:%S')}</span>
          </p>
        </div>
        """

        ActivityLogModel.objects.create(
            log=log,
        )

        messages.success(request, f"Payment of ₦{payment.amount} for {student.surname} {student.last_name} confirmed successfully.")
        return redirect(reverse('deposit_index')) # Replace with your actual URL name

    else:
        # For GET requests to this URL, you might want to display a confirmation prompt
        # or just redirect with a message. Assuming redirect for simplicity.
        messages.info(request, "Please use a POST request to confirm this payment.")
        return redirect(reverse('pending_deposit_index'))  # Replace with your actual URL name


# --- Decline Payment View ---
@login_required
@permission_required("student.change_studentfundingmodel", raise_exception=True)
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

        # Log wallet deposit decline
        from pytz import timezone as pytz_timezone
        localized_created_at = timezone.localtime(now(), timezone=pytz_timezone('Africa/Lagos'))
        formatted_time = localized_created_at.strftime(
            f"%B {localized_created_at.day}{get_day_ordinal_suffix(localized_created_at.day)} %Y %I:%M%p"
        )

        student_url = reverse('student_detail', kwargs={'pk': student.pk})
        payment_url = reverse('deposit_detail', kwargs={'pk': payment.pk})
        staff = UserProfileModel.objects.get(user=request.user).staff
        staff_url = reverse('staff_detail', kwargs={'pk': staff.pk}) if staff else '#'

        log = f"""
        <div class='text-white bg-danger p-2' style='border-radius:5px;'>
          <p>
            Payment of <a href="{payment_url}"><b>₦{payment.amount:.2f}</b></a> for
            <a href="{student_url}"><b>{student.__str__().title()}</b></a> was
            <b>declined</b> by
            <a href="{staff_url}"><b>{staff.__str__().title()}</b></a>.
            <br>
            <b>Status:</b> Declined
            <span class='float-end'>{now().strftime('%Y-%m-%d %H:%M:%S')}</span>
          </p>
        </div>
        """

        ActivityLogModel.objects.create(
            log=log,
        )

        messages.success(request, f"Payment of ₦{payment.amount} for {student.surname} {student.last_name} has been declined.")
        return redirect(reverse('deposit_index'))  # Replace with your actual URL name
    else:
        # For GET requests to this URL, you might want to display a confirmation prompt
        # or just redirect with a message. Assuming redirect for simplicity.
        messages.info(request, "Method Not Supported.")
        return redirect(reverse('pending_deposit_index'))  # Replace with your actual URL name


@csrf_exempt
def capture_fingerprint(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            finger_name = data.get('finger_name')
            fingerprint_data = data.get('fingerprint_data')

            student = StudentModel.objects.get(id=student_id)

            FingerprintModel.objects.create(
                student=student,
                finger_name=finger_name,
                fingerprint_data=fingerprint_data
            )

            return JsonResponse({'success': True, 'message': 'Fingerprint saved successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)


def match_fingerprint(input_template_b64: str, stored_template_bytes: bytes) -> bool:
    """
    Decode the incoming base64 template and compare it to stored bytes.
    Replace the pseudocode with your scanner SDK’s match() function.
    """
    try:
        probe = base64.b64decode(input_template_b64)
    except Exception:
        return False

    # --- PSEUDOCODE: swap this for your real SDK call! ---
    # e.g. result = your_sdk.verify(probe, stored_template_bytes)
    # return result.is_match
    #
    # For now we’ll just compare raw bytes (never true in real life)
    return probe == stored_template_bytes
# -----------------------------------------------------------------------------

@csrf_exempt
@require_POST
def identify_student_by_fingerprint(request):
    """
    Expects JSON: { "fingerprint_data": "<base64 template>" }
    Returns JSON with student info on match.
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

    template_b64 = payload.get('fingerprint_data')
    if not template_b64:
        return JsonResponse({'success': False, 'message': 'No fingerprint data provided'}, status=400)

    # Iterate all stored fingerprints
    for fp in FingerprintModel.objects.select_related('student').all():
        if match_fingerprint(template_b64, fp.fingerprint_data):
            stu = fp.student
            # Build student payload
            return JsonResponse({
                'success': True,
                'student': {
                    'id':             stu.id,
                    'name':           getattr(stu, 'full_name', str(stu)),
                    'reg_number':     getattr(stu, 'registration_number', ''),
                    'student_class':  getattr(stu, 'student_class', ''),
                    'wallet_balance': float(getattr(stu.student_wallet, 'balance', 0)),
                    'wallet_debt':    float(getattr(stu.student_wallet, 'debt', 0)),
                    'meal':    float(getattr(stu.student_wallet, 'meal', 0)),
                    'image_url':      stu.image.url if getattr(stu, 'image', None) else '',
                }
            })

    return JsonResponse({'success': False, 'message': 'Fingerprint not recognized'}, status=404)


def convert_money_ticket(request):
    student_id = request.POST.get('student_id')
    student = StudentModel.objects.get(pk=student_id)
    wallet = StudentWalletModel.objects.get(student=student)
    amount = float(request.POST.get('amount'))
    site_setting = SchoolSettingModel.objects.first()
    if not site_setting:
        messages.error(request, 'Setting not found, conversion not possible')
        return redirect(reverse('student_detail', kwargs={'pk': student_id}))
    total_cost = site_setting.meal_cost * amount
    if total_cost > wallet.balance:
        messages.error(request, 'Insufficient fund for conversion')
        return redirect(reverse('student_detail', kwargs={'pk': student_id}))

    wallet.balance -= total_cost
    wallet.meal += amount
    wallet.save()

    messages.success(request, 'Meal Tickets Bought Successfully')
    return redirect(reverse('student_detail', kwargs={'pk': student_id}))
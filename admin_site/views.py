import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.messages.views import SuccessMessageMixin, messages
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth import authenticate, login
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.sessions.models import Session
from admin_site.models import *
from django.db.models import Q, Count, F, Sum
from datetime import datetime, date
from urllib.parse import urlencode
from django.contrib.auth import logout
from django.http import HttpResponse
from admin_site.models import *
from admin_site.forms import *
from collections import OrderedDict
from django.utils.timezone import now

from human_resource.models import StaffModel
from inventory.models import ProductModel, SaleModel, SaleItemModel, ReturnModel, SupplierModel
from student.models import StudentModel


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_site/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['student_class_list'] = ClassSectionInfoModel.objects.all()

        context['total_products'] = ProductModel.objects.count()
        context['low_stock'] = ProductModel.objects.filter(quantity__lte=F('reorder_level')).count()
        context['total_sales_today'] = \
            SaleModel.objects.filter(sale_date__date=now().date()).aggregate(Sum('total_amount'))[
                'total_amount__sum'] or 0
        context['total_profit_today'] = \
            SaleItemModel.objects.filter(sale__sale_date__date=now().date()).aggregate(Sum('profit'))[
                'profit__sum'] or 0
        context['total_staff'] = StaffModel.objects.count()
        context['total_returns'] = ReturnModel.objects.count()
        context['total_suppliers'] = SupplierModel.objects.count()
        context['active_students'] = StudentModel.objects.filter(status='active').count()

        return context


def admin_sign_out_view(request):
    logout(request)
    return redirect(reverse('admin_login'))


class SchoolInfoDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_site/school_info/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_info = SchoolInfoModel.objects.first()

        if not school_info:
            form = SchoolInfoForm()
            is_school_info = False
        else:
            form = SchoolInfoForm(instance=school_info)
            is_school_info = True
        context['form'] = form
        context['is_school_info'] = is_school_info
        context['school_info'] = school_info
        return context


class SchoolInfoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SchoolInfoModel
    form_class = SchoolInfoForm
    template_name = 'admin_site/school_info/create.html'
    success_message = 'Info updated Successfully'

    def get_success_url(self):
        return reverse('school_info_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class SchoolInfoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SchoolInfoModel
    form_class = SchoolInfoForm
    template_name = 'admin_site/school_info/create.html'
    success_message = 'Info updated Successfully'

    def get_success_url(self):
        return reverse('school_info_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class SchoolSettingDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_site/school_setting/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school_setting = SchoolSettingModel.objects.first()

        if not school_setting:
            form = SchoolSettingForm()
            is_school_setting = False
        else:
            form = SchoolSettingForm(instance=school_setting)
            is_school_setting = True
        context['form'] = form
        context['is_school_setting'] = is_school_setting
        context['school_setting'] = school_setting
        return context


class SchoolSettingCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = SchoolSettingModel
    form_class = SchoolSettingForm
    template_name = 'admin_site/school_setting/create.html'
    success_message = 'Setting updated Successfully'

    def get_success_url(self):
        return reverse('school_setting_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class SchoolSettingUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SchoolSettingModel
    form_class = SchoolSettingForm
    template_name = 'admin_site/school_setting/create.html'
    success_message = 'Setting updated Successfully'

    def get_success_url(self):
        return reverse('school_setting_detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class ClassSectionCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = ClassSectionModel
    permission_required = 'admin_site.add_classsectionmodel'
    form_class = ClassSectionForm
    success_message = 'Class Section Added Successfully'
    template_name = 'admin_site/class_section/index.html'

    def get_success_url(self):
        return reverse('class_section_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_section_list'] = ClassSectionModel.objects.all().order_by('name')
        return context


class ClassSectionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ClassSectionModel
    permission_required = 'admin_site.view_classsectionmodel'
    fields = '__all__'
    template_name = 'admin_site/class_section/index.html'
    context_object_name = "class_section_list"

    def get_queryset(self):
        return ClassSectionModel.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ClassSectionForm
        return context


class ClassSectionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ClassSectionModel
    permission_required = 'admin_site.change_classsectionmodel'
    form_class = ClassSectionForm
    success_message = 'Class Section Updated Successfully'
    template_name = 'admin_site/class_section/index.html'

    def get_success_url(self):
        return reverse('class_section_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_section_list'] = ClassSectionModel.objects.all().order_by('name')
        return context


class ClassSectionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ClassSectionModel
    permission_required = 'admin_site.delete_classsectionmodel'
    success_message = 'Class Section Deleted Successfully'
    fields = '__all__'
    template_name = 'admin_site/class_section/delete.html'
    context_object_name = "class_section"

    def get_success_url(self):
        return reverse('class_section_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ClassCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = ClassesModel
    permission_required = 'academic.add_classesmodel'
    form_class = ClassForm
    success_message = 'Class Added Successfully'
    template_name = 'academic/class/index.html'

    def get_success_url(self):
        return reverse('class_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_list'] = ClassesModel.objects.all().order_by('name')
        context['class_section_list'] = ClassSectionModel.objects.all().order_by('name')
        return context


class ClassListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ClassesModel
    permission_required = 'admin_site.view_classesmodel'
    fields = '__all__'
    template_name = 'admin_site/class/index.html'
    context_object_name = "class_list"

    def get_queryset(self):
        return ClassesModel.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_section_list'] = ClassSectionModel.objects.all()
        context['form'] = ClassForm
        return context


class ClassDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ClassesModel
    permission_required = 'admin_site.view_classesmodel'
    fields = '__all__'
    template_name = 'admin_site/class/detail.html'
    context_object_name = "class"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['class_section_list'] = ClassSectionModel.objects.all()
        context['class_list'] = ClassesModel.objects.filter().order_by('name')
        return context


class ClassUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ClassesModel
    permission_required = 'admin_site.change_classsesmodel'
    form_class = ClassForm
    success_message = 'Class Updated Successfully'
    template_name = 'admin_site/class/index.html'

    def get_success_url(self):
        return reverse('class_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['class_list'] = ClassesModel.objects.all().order_by('name')
        return context


class ClassDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ClassesModel
    permission_required = 'admin_site.delete_classesmodel'
    success_message = 'Class Deleted Successfully'
    fields = '__all__'
    template_name = 'admin_site/class/delete.html'
    context_object_name = "class"

    def get_success_url(self):
        return reverse('class_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class TeacherCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = TeacherModel
    permission_required = 'admin_site.add_teachermodel'
    form_class = TeacherForm
    success_message = 'Teacher Added Successfully'
    template_name = 'admin_site/teacher/index.html'

    def get_success_url(self):
        return reverse('teacher_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher_list'] = TeacherModel.objects.all().order_by('full_name')
        return context


class TeacherListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TeacherModel
    permission_required = 'admin_site.view_teachermodel'
    fields = '__all__'
    template_name = 'admin_site/teacher/index.html'
    context_object_name = "teacher_list"

    def get_queryset(self):
        return TeacherModel.objects.all().order_by('full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TeacherForm

        return context


class TeacherUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = TeacherModel
    permission_required = 'admin_site.change_teachermodel'
    form_class = TeacherForm
    success_message = 'Teacher Updated Successfully'
    template_name = 'admin_site/teacher/index.html'

    def get_success_url(self):
        return reverse('teacher_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teacher_list'] = TeacherModel.objects.all().order_by('full_name')
        return context


class TeacherDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = TeacherModel
    permission_required = 'admin_site.delete_teachermodel'
    success_message = 'Teacher Deleted Successfully'
    fields = '__all__'
    template_name = 'admin_site/teacher/delete.html'
    context_object_name = "teacher"

    def get_success_url(self):
        return reverse("teacher_index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ClassSectionInfoCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = ClassSectionInfoModel
    permission_required = 'admin_site.add_classsectioninfomodel'
    form_class = ClassSectionInfoForm
    success_message = 'Class Section Info Updated Successfully'
    template_name = 'admin_site/class_section_info/detail.html'

    def get_success_url(self):
        return reverse('class_section_info_detail',
                       kwargs={'class_pk': self.object.student_class.pk, 'section_pk': self.object.section.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class ClassSectionInfoDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'admin_site.change_classsectioninfomodel'
    form_class = ClassSectionForm
    success_message = 'Class Section Updated Successfully'
    template_name = 'admin_site/class_section_info/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_pk = self.kwargs.get('class_pk')
        context['student_class'] = ClassesModel.objects.get(pk=class_pk)
        section_pk = self.kwargs.get('section_pk')
        context['class_section'] = ClassSectionModel.objects.get(pk=section_pk)
        context['class_section_info'] = ClassSectionInfoModel.objects.filter(student_class=context['student_class'],
                                                                             section=context['class_section']).first()
        context['staff_list'] = TeacherModel.objects.all().order_by('full_name')

        context['form'] = ClassSectionInfoForm
        return context


class ClassSectionInfoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ClassSectionInfoModel
    permission_required = 'admin_site.change_classsectioninfomodel'
    form_class = ClassSectionInfoForm
    success_message = 'Class Section Info Updated Successfully'
    template_name = 'admin_site/class_section_info/detail.html'

    def get_success_url(self):
        return reverse('class_section_info_detail',
                       kwargs={'class_pk': self.object.student_class.pk, 'section_pk': self.object.section.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

from django.contrib.auth.models import Permission
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
import json
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
import io
from django.forms.models import model_to_dict
from xlsxwriter.workbook import Workbook
from human_resource.models import *
from human_resource.forms import *
from django.db.models import Sum


class StaffCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = StaffModel
    permission_required = 'human_resource.add_staffmodel'
    form_class = StaffForm
    template_name = 'human_resource/staff/create.html'
    success_message = 'Staff Successfully Registered'

    def get_success_url(self):
        return reverse('staff_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class StaffListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StaffModel
    permission_required = 'human_resource.view_staffmodel'
    fields = '__all__'
    template_name = 'human_resource/staff/index.html'
    context_object_name = "staff_list"

    def get_queryset(self):
        return StaffModel.objects.filter(status='active').order_by('surname')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class StaffDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = StaffModel
    permission_required = 'human_resource.view_staffmodel'
    fields = '__all__'
    template_name = 'human_resource/staff/detail.html'
    context_object_name = "staff"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class StaffUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = StaffModel
    permission_required = 'human_resource.change_staffmodel'
    form_class = StaffForm
    template_name = 'human_resource/staff/edit.html'
    success_message = 'Staff Information Successfully Updated'

    def get_success_url(self):
        return reverse('staff_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['staff'] = self.object
        return context


class StaffDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = StaffModel
    permission_required = 'human_resource.delete_staffmodel'
    fields = '__all__'
    template_name = 'human_resource/staff/delete.html'
    context_object_name = "staff"
    success_message = 'Staff Successfully Deleted'

    def get_success_url(self):
        return reverse('staff_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Group
    permission_required = 'auth.add_group'
    form_class = GroupForm
    template_name = 'human_resource/group/list.html'
    success_message = 'Group Added Successfully'

    def get_success_url(self):
        return reverse('group_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    permission_required = 'auth.add_group'
    fields = '__all__'
    template_name = 'human_resource/group/index.html'
    context_object_name = "group_list"

    def get_queryset(self):
        return Group.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = GroupForm
        return context


class GroupDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Group
    permission_required = 'auth.add_group'
    fields = '__all__'
    template_name = 'human_resource/group/detail.html'
    context_object_name = "group"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Group
    permission_required = 'auth.add_group'
    form_class = GroupForm
    template_name = 'human_resource/group/index.html'
    success_message = 'Group Successfully Updated'

    def get_success_url(self):
        return reverse('group_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.object
        context['group_list'] = Group.objects.all().order_by('name')
        return context


class GroupPermissionView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Group
    permission_required = 'auth.add_group'
    form_class = GroupForm
    template_name = 'human_resource/group/permission.html'
    success_message = 'Group Permission Successfully Updated'

    def get_success_url(self):
        return reverse('group_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = self.object
        context['permission_list'] = Permission.objects.all()
        return context


@login_required
@permission_required("auth.add_group", raise_exception=True)
def group_permission_view(request, pk):
    group = Group.objects.get(pk=pk)
    if request.method == 'POST':
        permissions = request.POST.getlist('permissions[]')
        permission_list = []
        for permission_code in permissions:
            permission = Permission.objects.filter(codename=permission_code).first()
            if permission:
                permission_list.append(permission.id)
        group.permissions.set(permission_list)
        messages.success(request, 'Group Permission Successfully Updated')
        return redirect(reverse('group_index'))
    context = {
        'group': group,
        'permission_codenames': group.permissions.all().values_list('codename', flat=True),
        'permission_list': Permission.objects.all(),

    }
    return render(request, 'human_resource/group/permission.html', context)


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    permission_required = 'auth.add_group'
    fields = '__all__'
    template_name = 'human_resource/group/delete.html'
    context_object_name = "group"

    def get_success_url(self):
        return reverse('group_index')

    def dispatch(self, *args, **kwargs):
        if self.request.POST.get('name') in ['superadmin']:
            messages.error(self.request, 'Restricted Group, Permission Denied')
            return redirect(reverse('group_index'))
        return super(GroupDeleteView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

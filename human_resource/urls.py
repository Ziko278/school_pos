from django.urls import path
from human_resource.views import *

urlpatterns = [
    path('group/add', GroupCreateView.as_view(), name='group_create'),
    path('group/index', GroupListView.as_view(), name='group_index'),
    path('group/<int:pk>/detail', GroupDetailView.as_view(), name='group_detail'),
    path('group/<int:pk>/edit', GroupUpdateView.as_view(), name='group_edit'),
    path('group/<int:pk>/permission/edit', group_permission_view, name='group_permission'),
    path('group/<int:pk>/delete', GroupDeleteView.as_view(), name='group_delete'),

    path('staff/create', StaffCreateView.as_view(), name='staff_create'),
    path('staff/index', StaffListView.as_view(), name='staff_index'),
    path('staff/<int:pk>/detail', StaffDetailView.as_view(), name='staff_detail'),
    path('staff/<int:pk>/edit', StaffUpdateView.as_view(), name='staff_edit'),
    path('staff/<int:pk>/delete', StaffDeleteView.as_view(), name='staff_delete'),

]


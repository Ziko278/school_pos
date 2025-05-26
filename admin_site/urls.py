from django.urls import path
from admin_site.views import *

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='admin_dashboard'),

    path('school-info/<int:pk>', SchoolInfoDetailView.as_view(), name='school_info_detail'),
    path('school-info/create', SchoolInfoCreateView.as_view(), name='school_info_create'),
    path('school-info/<int:pk>/update', SchoolInfoUpdateView.as_view(), name='school_info_edit'),

    path('school-setting/<int:pk>', SchoolSettingDetailView.as_view(), name='school_setting_detail'),
    path('school-setting/create', SchoolSettingCreateView.as_view(), name='school_setting_create'),
    path('school-setting/<int:pk>/update', SchoolSettingUpdateView.as_view(), name='school_setting_edit'),

    path('class/section/create', ClassSectionCreateView.as_view(), name='class_section_create'),
    path('class/section/index', ClassSectionListView.as_view(), name='class_section_index'),
    path('class/section/<int:pk>/edit', ClassSectionUpdateView.as_view(), name='class_section_edit'),
    path('class/section/<int:pk>/delete', ClassSectionDeleteView.as_view(), name='class_section_delete'),

    path('class/create', ClassCreateView.as_view(), name='class_create'),
    path('class/index', ClassListView.as_view(), name='class_index'),
    path('class/<int:pk>/detail', ClassDetailView.as_view(), name='class_detail'),
    path('class/<int:pk>/edit', ClassUpdateView.as_view(), name='class_edit'),
    path('class/<int:pk>/delete', ClassDeleteView.as_view(), name='class_delete'),

    path('class/section/info/create', ClassSectionInfoCreateView.as_view(), name='class_section_info_create'),
    path('class/section/info/<int:class_pk>/<int:section_pk>/detail', ClassSectionInfoDetailView.as_view(),
         name='class_section_info_detail'),
    path('class/section/info/<int:pk>/edit', ClassSectionInfoUpdateView.as_view(), name='class_section_info_edit'),

    path('teacher/create', TeacherCreateView.as_view(), name='teacher_create'),
    path('teacher/index', TeacherListView.as_view(), name='teacher_index'),
    path('teacher/<int:pk>/edit', TeacherUpdateView.as_view(), name='teacher_edit'),
    path('teacher/<int:pk>/delete', TeacherDeleteView.as_view(), name='teacher_delete'),

]

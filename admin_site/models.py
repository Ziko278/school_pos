import random

from django.db import models
from django.contrib.auth.models import User
from django.apps import apps


class SessionModel(models.Model):
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    SEPERATOR = (('-', '-'), ('/', '/'))
    seperator = models.CharField(max_length=1, choices=SEPERATOR)

    def __str__(self):
        return str(round(self.start_year)) + self.seperator + str(round(self.end_year))


class SchoolInfoModel(models.Model):
    name = models.CharField(max_length=250)
    short_name = models.CharField(max_length=50)
    logo = models.FileField(upload_to='images/logo', blank=True)
    mobile = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.short_name.upper()


class SchoolSettingModel(models.Model):
    allow_student_debt = models.BooleanField(default=True)
    auto_low_balance_notification = models.BooleanField(default=True)
    max_student_debt = models.FloatField()
    low_balance = models.FloatField()
    allow_refund = models.BooleanField(default=False)
    auto_generate_student_id = models.BooleanField(default=True)
    session = models.ForeignKey(SessionModel, on_delete=models.SET_NULL, null=True, blank=True)
    TERM = (
        ('1st term', '1st TERM'), ('2nd term', '2nd TERM'), ('3rd term', '3rd TERM')
    )
    term = models.CharField(max_length=10, choices=TERM, null=True, blank=True)
    account_name = models.CharField(max_length=200, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    bank = models.CharField(max_length=100, null=True, blank=True)


class ClassSectionModel(models.Model):
    """  """
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_class_name_type_combo',
            )
        ]

    def __str__(self):
        return self.name.upper()


class ClassesModel(models.Model):
    """  """
    name = models.CharField(max_length=100, unique=True)
    section = models.ManyToManyField(ClassSectionModel, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name',],
                name='unique_name_class_type_combo'
            )
        ]

    def __str__(self):
        return self.name.upper()

    def number_of_students(self):
        StudentModel = apps.get_model('student', 'StudentModel')
        return StudentModel.objects.filter(student_class=self).count()


class TeacherModel(models.Model):
    """  """
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
    GENDER = (
        ('male', 'MALE'), ('female', 'FEMALE')
    )
    gender = models.CharField(max_length=10, choices=GENDER)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.full_name.upper()


class ClassSectionInfoModel(models.Model):
    """  """
    student_class = models.ForeignKey(ClassesModel, on_delete=models.CASCADE)
    section = models.ForeignKey(ClassSectionModel, blank=True, on_delete=models.CASCADE)
    form_teacher = models.ForeignKey(TeacherModel, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        ordering = []
        constraints = [
            models.UniqueConstraint(
                fields=['student_class', 'section'],
                name='unique_student_class_section_combo'
            )
        ]

    def __str__(self):
        return "{} {}".format(self.student_class.name.upper(), self.section.name.upper())

    def number_of_students(self):
        StudentModel = apps.get_model('student', 'StudentModel')
        return StudentModel.objects.filter(student_class=self.student_class, class_section=self.section).count()


class ActivityLogModel(models.Model):
    log = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    session = models.ForeignKey(SessionModel, on_delete=models.SET_NULL, null=True, blank=True)
    TERM = (
        ('1st term', '1st TERM'), ('2nd term', '2nd TERM'), ('3rd term', '3rd TERM')
    )
    term = models.CharField(max_length=10, choices=TERM, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.session or not self.term:
            setting = SchoolSettingModel.objects.first()
            self.session = setting.session
            self.term = setting.term

        super(ActivityLogModel, self).save(*args, **kwargs)

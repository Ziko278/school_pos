from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class UserProfileModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    staff = models.OneToOneField('human_resource.StaffModel', on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='account')
    student = models.OneToOneField('student.StudentModel', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='student_account')
    reference_id = models.IntegerField()
    reference = models.CharField(max_length=20)
    default_password = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

from django.db import models
from django.contrib.auth.models import User, Group
from user_site.models import UserProfileModel


class StaffModel(models.Model):
    """"""
    surname = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    image = models.FileField(upload_to='images/staff_images', blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, unique=True)

    GENDER = (
        ('MALE', 'MALE'), ('FEMALE', 'FEMALE')
    )
    gender = models.CharField(max_length=10, choices=GENDER)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    status = models.CharField(max_length=30, blank=True, default='active')

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.surname + ' ' + self.last_name

    def save(self, *args, **kwargs):
        try:
            user_profile = UserProfileModel.objects.get(staff__email=self.email)
            user = user_profile.user
            if self.email:
                user.email = self.email
            user.save()

            self.group.user_set.add(user)
        except Exception:
            pass

        super(StaffModel, self).save(*args, **kwargs)

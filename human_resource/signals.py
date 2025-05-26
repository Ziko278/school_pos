from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from human_resource.models import StaffModel
from django.contrib.auth.models import User
from user_site.models import UserProfileModel


@receiver(post_save, sender=StaffModel)
def create_staff_account(sender, instance, created, **kwargs):
    if created:
        staff = instance
        username = staff.email
        password = User.objects.make_random_password(length=8)
        email = staff.email

        user = User.objects.create_user(username=username, email=email, password=password, is_active=True, is_staff=True)
        user_profile = UserProfileModel.objects.create(user=user, reference_id=staff.id, staff=staff, reference='staff',
                                                       default_password=password)
        user_profile.save()

        staff.group.user_set.add(user)


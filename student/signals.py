from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from admin_site.models import SchoolInfoModel
from student.models import *
from django.contrib.auth.models import User
from student.models import StudentModel, StudentWalletModel
import secrets


def make_random_password(length=10, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
    return ''.join(secrets.choice(allowed_chars) for i in range(length))


@receiver(post_save, sender=StudentModel)
def create_student_account(sender, instance, created, **kwargs):
    if created:
        student = instance

        username = student.registration_number
        parent_username = 'p' + student.registration_number
        password = make_random_password(8)
        parent_password = make_random_password(8)
        email = student.email

        user = User.objects.create_user(username=username, email=email, password=password)
        user_profile = UserProfileModel.objects.create(user=user, reference_id=student.id, student=student,
                                                       reference='student',
                                                       default_password=password)
        user_profile.save()

        parent_user = User.objects.create_user(username=parent_username, email=email, password=parent_password)
        parent_user_profile = UserProfileModel.objects.create(user=parent_user, reference_id=student.id, parent=student,
                                                       reference='parent',
                                                       default_password=parent_password)
        parent_user_profile.save()

        wallet = StudentWalletModel.objects.create(student=student)
        wallet.save()

        school_info = SchoolInfoModel.objects.first()
        html_content = render_to_string(
            'student/mail/login_detail.html',
            {
                'username': parent_username,
                'password': parent_password,
             'student': student,
             'school_info': school_info,
             'domain':  settings.DOMAIN_NAME}
        )

        # Render plain text email
        text_content = f'Your Login Detail: username: {parent_username}, password: {parent_password}'

        # Create and send email
        subject = f'{school_info.name} Login Credential'
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()



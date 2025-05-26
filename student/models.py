import random
from django.contrib.auth.models import User
from django.db import models, transaction
from admin_site.models import ClassesModel, ClassSectionModel, SchoolSettingModel, SessionModel
from user_site.models import UserProfileModel
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from io import BytesIO
import barcode
from barcode.writer import ImageWriter


def generate_barcode(identifier):
    # Generate the barcode image as bytes
    buffer = BytesIO()
    code = barcode.Code39(identifier, writer=ImageWriter(), add_checksum=False)
    code.write(buffer)

    # Reset buffer position to the beginning
    buffer.seek(0)

    # Path inside your MEDIA_ROOT directory
    relative_path = f'barcode/student/{identifier}.png'

    # Create ContentFile from buffer and save locally
    barcode_image_file = ContentFile(buffer.read(), name=relative_path)
    default_storage.save(relative_path, barcode_image_file)

    # Return the media-relative URL
    return f'media/{relative_path}'


class StudentModel(models.Model):
    """"""
    surname = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    GENDER = (
        ('MALE', 'MALE'), ('FEMALE', 'FEMALE')
    )
    gender = models.CharField(max_length=10, choices=GENDER)
    image = models.FileField(blank=True, null=True, upload_to='images/student_images')
    mobile = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    student_class = models.ForeignKey(ClassesModel, null=True, on_delete=models.CASCADE)
    class_section = models.ForeignKey(ClassSectionModel, null=True, on_delete=models.CASCADE)
    barcode = models.FileField(upload_to='barcode/student', null=True, blank=True)
    status = models.CharField(max_length=15, blank=True, default='active')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.surname} {self.last_name}"

    def save(self, *args, **kwargs):
        with transaction.atomic():  # Ensuring atomicity for the entire save operation

            # Generate registration number if required
            school_setting = SchoolSettingModel.objects.first()
            if school_setting.auto_generate_student_id and not self.registration_number:
                while True:
                    random_numbers = [random.randint(0, 9999), random.randint(0, 9999)]
                    student_id = f"stu-{random_numbers[0]:04}-{random_numbers[1]:04}"
                    student_exist = StudentModel.objects.filter(registration_number=student_id).first()
                    if not student_exist:
                        break

                self.registration_number = student_id

            # Handle user account creation
            if self.id:
                try:
                    # Check if a user profile exists for the student
                    user_profile = UserProfileModel.objects.get(student_id=self.id)
                    user = user_profile.user
                    user.username = self.registration_number  # Update username to match registration number
                    if self.email:
                        user.email = self.email  # Update email if provided
                    user.save()  # Save updated user details
                except UserProfileModel.DoesNotExist:
                    # Create a new user account if no profile exists
                    username = self.registration_number
                    email = self.email
                    password = User.objects.make_random_password(length=8)  # Generate random password
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={'email': email, 'password': password}
                    )
                    if created:
                        user.set_password(password)  # Set the generated password
                        user.save()
                        # Create a new user profile
                        UserProfileModel.objects.create(
                            user=user,
                            student=self,
                            default_password=password,
                            reference='student',
                            reference_id=self.id
                        )
            if self.registration_number and not self.barcode:
                barcode_file_path = generate_barcode(self.registration_number)
                self.barcode = barcode_file_path

        super().save(*args, **kwargs)


class StudentWalletModel(models.Model):
    student = models.OneToOneField(StudentModel, on_delete=models.CASCADE, blank=True, related_name='student_wallet')
    balance = models.FloatField(default=0.0)
    debt = models.FloatField(default=0.0)

    def __str__(self):
        return self.student.__str__()


class StudentFundingModel(models.Model):
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE, blank=True, related_name='funding_list')
    amount = models.FloatField()
    balance = models.FloatField(default=0, blank=True)
    proof_of_payment = models.FileField(blank=True, null=True, upload_to='images/funding')
    METHOD = (
        ('cash', 'CASH'), ('pos', 'POS'), ('bank teller', 'BANK TELLER'), ('bank transfer', 'BANK TRANSFER')
    )
    method = models.CharField(max_length=100, choices=METHOD, blank=True, default='cash')
    MODE = (('offline', 'OFFLINE'), ('online', 'ONLINE'))
    mode = models.CharField(max_length=100, choices=MODE, blank=True, default='offline')
    status = models.CharField(max_length=30, blank=True, default='confirmed')  # pending, failed and completed
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    session = models.ForeignKey(SessionModel, on_delete=models.SET_NULL, null=True, blank=True)
    TERM = (
        ('1st term', '1st TERM'), ('2nd term', '2nd TERM'), ('3rd term', '3rd TERM')
    )
    term = models.CharField(max_length=10, choices=TERM, null=True, blank=True)

    def __str__(self):
        return f"{self.student.__str__() - self.amount}"

    def save(self, *args, **kwargs):
        if not self.session or not self.term:
            setting = SchoolSettingModel.objects.first()
            self.session = setting.session
            self.term = setting.term

        super(StudentFundingModel, self).save(*args, **kwargs)

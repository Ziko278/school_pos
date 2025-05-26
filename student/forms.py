from django.contrib.auth import forms
from django.forms import ModelForm, Select, TextInput, DateInput
from student.models import StudentModel, StudentFundingModel


class StudentForm(ModelForm):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        boolean_fields = ['is_new']
        for field in self.fields:
            if field not in boolean_fields:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    def clean(self):
        cleaned_data = super().clean()
        registration_number = cleaned_data.get('registration_number')

        if registration_number:
            # Check if the registration number already exists
            if StudentModel.objects.filter(registration_number=registration_number).exists():
                raise forms.ValidationError({
                    'registration_number': f'A student with this registration number {registration_number} already exists.'
                })

        return cleaned_data

    class Meta:
        model = StudentModel
        fields = '__all__'
        exclude = []
        widgets = {

        }


class StudentFundingForm(ModelForm):
    """"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })

    class Meta:
        model = StudentFundingModel
        fields = '__all__'
        widgets = {

        }

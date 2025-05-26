from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Select, TextInput, CheckboxInput, CheckboxSelectMultiple, DateInput
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from admin_site.models import *
from django.contrib.auth.models import Group


class GroupForm(ModelForm):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })

    class Meta:
        model = Group
        fields = '__all__'

        widgets = {

        }


class SchoolInfoForm(ModelForm):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            if field != 'separate_school_section':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    class Meta:
        model = SchoolInfoModel
        fields = '__all__'

        widgets = {
            'active_days': CheckboxSelectMultiple(attrs={

            })
        }


class SchoolSettingForm(ModelForm):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        boolean_data = ['allow_student_debt', 'auto_low_balance_notification', 'auto_generate_student_id',
                        'allow_refund']
        for field in self.fields:
            if field not in boolean_data:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    class Meta:
        model = SchoolSettingModel
        exclude = ['session', 'term']

        widgets = {

        }


class ClassSectionForm(ModelForm):
    """  """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })

    class Meta:
        model = ClassSectionModel
        fields = '__all__'

        widgets = {

        }


class ClassForm(ModelForm):
    """   """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'section' and field != 'is_graduation_class':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    class Meta:
        model = ClassesModel
        fields = '__all__'

        widgets = {
            'section': CheckboxSelectMultiple(attrs={

            })
        }


class TeacherForm(ModelForm):
    """  """
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'subjects' and field != 'student_class':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    class Meta:
        model = TeacherModel
        fields = '__all__'

        widgets = {

        }


class ClassSectionInfoForm(ModelForm):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields:
            if field != 'section' and field != 'subjects':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    class Meta:
        model = ClassSectionInfoModel
        fields = '__all__'
        widgets = {

        }
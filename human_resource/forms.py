from django.forms import ModelForm, Select, TextInput, DateInput, CheckboxInput
from human_resource.models import *


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


class StaffForm(ModelForm):
    """  """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['group'].queryset = Group.objects.exclude(name='student').exclude(name='parent').order_by('name')
        for field in self.fields:
            if field != 'can_teach':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    class Meta:
        model = StaffModel
        fields = '__all__'
        widgets = {

        }




from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Select, TextInput, CheckboxInput, CheckboxSelectMultiple, DateInput, \
    modelformset_factory, inlineformset_factory
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from inventory.models import *
from django.contrib.auth.models import Group


class CategoryForm(ModelForm):
    """   """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })

    class Meta:
        model = CategoryModel
        fields = '__all__'

        widgets = {
            'section': CheckboxSelectMultiple(attrs={

            })
        }


class ProductForm(ModelForm):
    """   """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })

    class Meta:
        model = ProductModel
        fields = '__all__'

        widgets = {
            'section': CheckboxSelectMultiple(attrs={

            })
        }
        
        
class SupplierForm(ModelForm):
    """   """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'products':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'autocomplete': 'off'
                })

    class Meta:
        model = SupplierModel
        fields = '__all__'

        widgets = {
            'products': CheckboxSelectMultiple(attrs={

            })
        }


class StockInSummaryForm(forms.ModelForm):
    class Meta:
        model = StockInSummaryModel
        # ONLY include 'date' as per your StockInSummaryModel definition
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'date': 'Receipt Date',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial['date'] = timezone.now().strftime('%Y-%m-%d')


class StockInItemForm(forms.ModelForm):
    class Meta:
        model = StockInModel
        fields = ['product', 'quantity_added', 'unit_cost_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select'}),
            'quantity_added': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'required': True}),
            'unit_cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.00', 'required': True}),
        }
        labels = {
            'product': 'Product',
            'quantity_added': 'Quantity Received',
            'unit_cost_price': 'Unit Cost',
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity_added = cleaned_data.get('quantity_added')
        unit_cost_price = cleaned_data.get('unit_cost_price')

        # Only validate if the form is not marked for deletion (important for formsets)
        if not self.cleaned_data.get('DELETE', False):
            if product and (quantity_added is None or quantity_added <= 0):
                self.add_error('quantity_added', 'Quantity must be greater than zero.')
            if product and (unit_cost_price is None or unit_cost_price < 0):
                self.add_error('unit_cost_price', 'Unit cost cannot be negative.')

        return cleaned_data


StockInFormSet = modelformset_factory(
    StockInModel,
    form=StockInItemForm,
    extra=1,
    can_delete=True,
    fields=['product', 'quantity_added', 'unit_cost_price']
)


class SaleForm(forms.ModelForm):
    class Meta:
        model = SaleModel
        fields = ['student', 'sale_date', 'term']
        widgets = {
            'sale_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItemModel
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01'}),
        }

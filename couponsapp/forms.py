from django import forms
from .models import Coupon
from django.utils import timezone

class CouponForm(forms.ModelForm):
    error_css_class = 'error'  # Add a custom CSS class for errors
    required_css_class = 'required'  # Add a custom CSS class for required fields

    class Meta:
        model = Coupon
        fields = [
            'coupon_code', 'minimum_purchase_amount', 'discount_percentage',
            'valid_from', 'valid_to'
        ]
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valid_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'coupon_code': forms.TextInput(attrs={'class': 'form-control'}),
            'minimum_purchase_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_discount_percentage(self):
        discount_percentage = self.cleaned_data.get('discount_percentage')
        if discount_percentage < 0:
            raise forms.ValidationError("Discount percentage cannot be negative.")
        return discount_percentage
    
    def clean_minimum_purchase_amount(self):
        minimum_purchase_amount = self.cleaned_data.get('minimum_purchase_amount')
        if minimum_purchase_amount < 0:
            raise forms.ValidationError("Minimum purchase amount cannot be negative.")
        return minimum_purchase_amount

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        instance = getattr(self, 'instance', None)  # Get the instance being edited

        # Debugging: Print changed data and initial values
        print("Changed data:", self.changed_data)
        print("Initial valid_from:", getattr(instance, 'valid_from', None))
        print("Initial valid_to:", getattr(instance, 'valid_to', None))

        if instance and instance.pk:
            # Check if valid_from is being changed
            if 'valid_from' in self.changed_data:
                if valid_from and valid_from < timezone.now().date():
                    self.add_error('valid_from', 'Valid from date cannot be in the past.')

            # Check if valid_to is being changed
            if 'valid_to' in self.changed_data:
                if valid_to and valid_from and valid_to <= valid_from:
                    self.add_error('valid_to', 'Valid to date must be after valid from date.')
        else:
            # For new coupons, enforce the usual validation rules
            if valid_from and valid_from < timezone.now().date():
                self.add_error('valid_from', 'Valid from date cannot be in the past.')

            if valid_to and valid_from and valid_to <= valid_from:
                self.add_error('valid_to', 'Valid to date must be after valid from date.')

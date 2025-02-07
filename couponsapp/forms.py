# from django import forms
# from .models import Coupon

# class CouponForm(forms.ModelForm):
#     class Meta:
#         model = Coupon
#         fields = [
#             'coupon_code', 'minimum_purchase_amount', 'discount_percentage',
#             'valid_from', 'valid_to'
#         ]
#         widgets = {
#             'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
#             'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
#             'coupon_code': forms.TextInput(attrs={'class': 'form-control'}),
#             'minimum_purchase_amount': forms.NumberInput(attrs={'class': 'form-control'}),
#             'discount_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
#         }
    

from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'coupon_code', 'minimum_purchase_amount', 'discount_percentage',
            'valid_from', 'valid_to'
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
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
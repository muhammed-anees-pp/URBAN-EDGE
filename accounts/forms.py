# # from django import forms
# # from .models import User


# # class SignupForm(forms.ModelForm):
# #     password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), label="Password")
# #     confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}), label="Confirm Password")

# #     class Meta:
# #         model = User
# #         fields = ['first_name', 'last_name', 'username', 'email', 'password']

# #     def __init__(self, *args, **kwargs):
# #         super(SignupForm, self).__init__(*args, **kwargs)
# #         self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
# #         self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
# #         self.fields['username'].widget.attrs['placeholder'] = 'Username'
# #         self.fields['email'].widget.attrs['placeholder'] = 'Email'

# #     def clean(self):
# #         cleaned_data = super().clean()
# #         password = cleaned_data.get('password')
# #         confirm_password = cleaned_data.get('confirm_password')
# #         if password != confirm_password:
# #             raise forms.ValidationError("Passwords do not match")
# #         return cleaned_data

# from django import forms
# from django.contrib.auth.models import User
# from .models import UserDetails

# class SignupForm(forms.ModelForm):
#     """
#     A form for registering new users.
#     """
#     password = forms.CharField(widget=forms.PasswordInput)
#     confirm_password = forms.CharField(widget=forms.PasswordInput)

#     class Meta:
#         model = User
#         fields = ['username', 'email', 'first_name', 'last_name', 'password']

#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get('password')
#         confirm_password = cleaned_data.get('confirm_password')
#         if password != confirm_password:
#             raise forms.ValidationError("Passwords do not match.")
#         return cleaned_data

# class LoginForm(forms.Form):
#     username = forms.CharField(max_length=50)
#     password = forms.CharField(widget=forms.PasswordInput)

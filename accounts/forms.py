from django import forms
from django.contrib.auth.forms import AuthenticationForm
from phonenumber_field.formfields import PhoneNumberField

class PhoneAuthenticationForm(AuthenticationForm):
    # Overriding the default username field with a smart international phone field
    username = PhoneNumberField(
        region="ZM",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 097xxxxxxx or +260...',
            'style': 'width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;'
        }),
        label="Phone Number"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'style': 'width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;'
        })
    )


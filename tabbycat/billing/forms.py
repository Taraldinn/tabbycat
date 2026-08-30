from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Payment


class ManualPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method', 'sender_phone', 'transaction_id', 'payment_screenshot']
        widgets = {
            'method': forms.Select(attrs={'class': 'form-control custom-select'}),
            'sender_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01XXXXXXXXX'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9B8C7D6E5F'}),
            'payment_screenshot': forms.FileInput(attrs={'class': 'custom-file-input', 'id': 'customFile'}),
        }

    def clean_sender_phone(self):
        phone = self.cleaned_data.get('sender_phone', '').strip()
        if not phone:
            raise forms.ValidationError(_("Sender phone number is required."))
        return phone

    def clean_transaction_id(self):
        trx = self.cleaned_data.get('transaction_id', '').strip()
        if not trx:
            raise forms.ValidationError(_("Transaction ID (TrxID) is required."))
        return trx

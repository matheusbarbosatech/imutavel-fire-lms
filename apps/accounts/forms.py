from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from validate_docbr import CPF
from .models import CustomUser

cpf_validator = CPF()

class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    email = forms.EmailField(required=True, label="E-mail")
    cpf = forms.CharField(max_length=14, required=True, label="CPF", help_text="Digite apenas os números")

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'cpf']

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '').replace('.', '').replace('-', '').strip()
        if not cpf_validator.validate(cpf):
            raise forms.ValidationError("Número de CPF inválido.")
        if CustomUser.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError("Este CPF já está cadastrado no sistema.")
        return cpf


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'rg', 'cbmerj_registration']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'cbmerj_registration': forms.TextInput(attrs={'class': 'form-control'}),
        }
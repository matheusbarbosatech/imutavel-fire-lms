from django import forms
from .models import Matricula, Documento

class Step1Form(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ['nome', 'cpf', 'rg', 'nascimento']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000-0'}),
            'nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        }

class Step2Form(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ['email', 'telefone', 'endereco']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Rua, número, bairro, cidade - UF'})
        }

class Step3Form(forms.Form):
    # ✅ REMOVIDO: foto_file (não é mais necessário)
    rg_file = forms.FileField(
        label='RG (Frente e Verso)',
        help_text='Envie um arquivo PDF ou imagem legível do RG',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,application/pdf'})
    )
    cpf_file = forms.FileField(
        label='CPF',
        help_text='Envie um arquivo PDF ou imagem legível do CPF',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,application/pdf'})
    )

class Step4Form(forms.Form):
    aceitou_termos = forms.BooleanField(
        required=True,
        label=(
            '✅ Declaro que todas as informações prestadas são verdadeiras, '
            'que os documentos anexados estão legíveis e autorizo o tratamento '
            'dos meus dados conforme a LGPD para fins de matrícula.'
        ),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input me-2'})
    )
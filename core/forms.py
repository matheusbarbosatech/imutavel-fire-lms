from django import forms
from .models import Matricula, Documento

class Step1Form(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ['nome', 'cpf', 'rg', 'nascimento']
        widgets = {'nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})}

class Step2Form(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ['email', 'telefone', 'endereco']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class Step3Form(forms.Form):
    rg_file = forms.FileField(label='RG (Frente e Verso)', widget=forms.FileInput(attrs={'class': 'form-control'}))
    cpf_file = forms.FileField(label='CPF', widget=forms.FileInput(attrs={'class': 'form-control'}))
    foto_file = forms.FileField(label='Foto 3x4 Recente', widget=forms.FileInput(attrs={'class': 'form-control'}))

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
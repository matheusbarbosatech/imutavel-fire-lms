import os
from pathlib import Path
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import Step1Form, Step2Form, Step3Form, Step4Form
from .models import Matricula, Documento

# Garante pasta de uploads temporários
TMP_UPLOADS_DIR = Path(settings.BASE_DIR) / 'tmp_uploads'
TMP_UPLOADS_DIR.mkdir(exist_ok=True)

def _date_to_str(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    return obj

def _str_to_date(value):
    if isinstance(value, str) and len(value) == 10 and value[4] == '-' and value[7] == '-':
        try:
            return date.fromisoformat(value)
        except:
            return value
    return value

def _clean_session(request):
    for k in ['step1', 'step2', 'temp_files']:
        if k in request.session:
            del request.session[k]

def passo_1(request):
    if request.method == 'POST':
        form = Step1Form(request.POST)
        if form.is_valid():
            data = {k: _date_to_str(v) for k, v in form.cleaned_data.items()}
            request.session['step1'] = data
            return redirect('passo_2')
    else:
        raw = request.session.get('step1', {})
        initial = {k: _str_to_date(v) for k, v in raw.items()}
        form = Step1Form(initial=initial)
    return render(request, 'core/step.html', {'form': form, 'step': 1, 'title': '📋 Dados Pessoais'})

def passo_2(request):
    if 'step1' not in request.session:
        return redirect('passo_1')
    if request.method == 'POST':
        form = Step2Form(request.POST)
        if form.is_valid():
            request.session['step2'] = form.cleaned_data
            return redirect('passo_3')
    else:
        form = Step2Form(initial=request.session.get('step2', {}))
    return render(request, 'core/step.html', {'form': form, 'step': 2, 'title': '📍 Contato e Endereço'})

def passo_3(request):
    if 'step2' not in request.session:
        return redirect('passo_2')
    TMP_UPLOADS_DIR.mkdir(exist_ok=True)
    
    if request.method == 'POST':
        form = Step3Form(request.POST, request.FILES)
        if form.is_valid():
            tmp = {}
            for key, f in form.cleaned_data.items():
                with open(TMP_UPLOADS_DIR / f"{request.session.session_key}_{key}.{f.name.split('.')[-1]}", 'wb+') as tf:
                    for chunk in f.chunks():
                        tf.write(chunk)
                tmp[key] = str(TMP_UPLOADS_DIR / tf.name)
            request.session['temp_files'] = tmp
            return redirect('passo_4')
    else:
        form = Step3Form()
    return render(request, 'core/step.html', {'form': form, 'step': 3, 'title': '📎 Upload de Documentos'})

def passo_4(request):
    if 'temp_files' not in request.session:
        return redirect('passo_3')
    if request.method == 'POST':
        form = Step4Form(request.POST)
        if form.is_valid():
            s1_raw = request.session['step1']
            s1 = {k: _str_to_date(v) for k, v in s1_raw.items()}
            s2 = request.session['step2']
            
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
            ua = request.META.get('HTTP_USER_AGENT', 'unknown')[:500]
            
            mat = Matricula.objects.create(
                nome=s1['nome'], cpf=s1['cpf'], rg=s1['rg'], nascimento=s1['nascimento'],
                email=s2['email'], telefone=s2['telefone'], endereco=s2['endereco'],
                aceitou_termos=True, ip_registro=ip, user_agent=ua
            )
            
            for key, path in request.session['temp_files'].items():
                tipo = key.replace('_file', '')
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        doc = Documento(matricula=mat, tipo=tipo)
                        doc.arquivo.save(f"{tipo}_{mat.id}.{path.split('.')[-1]}", f, save=True)
                    os.remove(path)
                    
            try:
                send_mail('Matrícula Recebida', f'Olá {mat.nome}, seu protocolo é #{mat.id}. Aguarde análise.', 
                          settings.DEFAULT_FROM_EMAIL, [mat.email], fail_silently=False)
            except:
                pass
                
            _clean_session(request)
            messages.success(request, '✅ Matrícula enviada com sucesso!')
            return redirect('sucesso')
    else:
        form = Step4Form()
    return render(request, 'core/step.html', {'form': form, 'step': 4, 'title': '✍️ Confirmação e Termos'})

def sucesso(request):
    return render(request, 'core/success.html')
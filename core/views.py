import os, uuid
from pathlib import Path
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.base import ContentFile
from supabase import create_client
from .forms import Step1Form, Step2Form, Step3Form, Step4Form
from .models import Matricula, Documento

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
    for k in ['step1', 'step2', 'uploaded_files']:
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
    
    if request.method == 'POST':
        form = Step3Form(request.POST, request.FILES)
        if form.is_valid():
            # ✅ SALVAR DIRETO NO SUPABASE (sem usar disco local)
            try:
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
                uploaded_files = {}
                
                for key, file in form.cleaned_data.items():
                    # Gerar nome único
                    file_ext = file.name.split('.')[-1]
                    file_name = f"temp/{uuid.uuid4().hex}.{file_ext}"
                    
                    # Upload direto para Supabase
                    file_content = file.read()
                    supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                        path=file_name,
                        file=file_content,
                        file_options={"content-type": file.content_type}
                    )
                    
                    # Salvar apenas o path na sessão (não o arquivo)
                    uploaded_files[key] = file_name
                
                request.session['uploaded_files'] = uploaded_files
                return redirect('passo_4')
                
            except Exception as e:
                messages.error(request, f'Erro ao fazer upload: {str(e)}')
                return redirect('passo_3')
    else:
        form = Step3Form()
    return render(request, 'core/step.html', {'form': form, 'step': 3, 'title': '📎 Upload de Documentos'})

def passo_4(request):
    if 'uploaded_files' not in request.session:
        return redirect('passo_3')
    
    if request.method == 'POST':
        form = Step4Form(request.POST)
        if form.is_valid():
            try:
                s1_raw = request.session['step1']
                s1 = {k: _str_to_date(v) for k, v in s1_raw.items()}
                s2 = request.session['step2']
                
                # Captura IP e User-Agent
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
                ua = request.META.get('HTTP_USER_AGENT', 'unknown')[:500]
                
                # Criar matrícula
                mat = Matricula.objects.create(
                    nome=s1['nome'], cpf=s1['cpf'], rg=s1['rg'], nascimento=s1['nascimento'],
                    email=s2['email'], telefone=s2['telefone'], endereco=s2['endereco'],
                    aceitou_termos=True, ip_registro=ip, user_agent=ua
                )
                
                # ✅ MOVER ARQUIVOS DE TEMP PARA PASTA FINAL
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
                
                for key, temp_path in request.session['uploaded_files'].items():
                    tipo = key.replace('_file', '')
                    
                    # Baixar do temp
                    file_content = supabase.storage.from_(settings.SUPABASE_BUCKET).download(temp_path)
                    
                    # Upload para pasta final
                    final_path = f"docs/{tipo}_{mat.id}.{temp_path.split('.')[-1]}"
                    supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                        path=final_path,
                        file=file_content,
                        file_options={"content-type": "application/octet-stream"}
                    )
                    
                    # Deletar arquivo temporário
                    supabase.storage.from_(settings.SUPABASE_BUCKET).remove([temp_path])
                    
                    # Criar registro no banco
                    Documento.objects.create(
                        matricula=mat,
                        tipo=tipo,
                        arquivo=final_path
                    )
                
                # Enviar e-mail
                try:
                    send_mail(
                        'Matrícula Recebida',
                        f'Olá {mat.nome}, seu protocolo é #{mat.id}. Aguarde análise.',
                        settings.DEFAULT_FROM_EMAIL,
                        [mat.email],
                        fail_silently=False
                    )
                except Exception as e:
                    # Se e-mail falhar, não interrompe o processo
                    print(f"Erro ao enviar e-mail: {e}")
                
                _clean_session(request)
                messages.success(request, '✅ Matrícula enviada com sucesso!')
                return redirect('sucesso')
                
            except Exception as e:
                messages.error(request, f'Erro ao finalizar matrícula: {str(e)}')
                return redirect('passo_4')
    else:
        form = Step4Form()
    return render(request, 'core/step.html', {'form': form, 'step': 4, 'title': '✍️ Confirmação e Termos'})

def sucesso(request):
    return render(request, 'core/success.html')
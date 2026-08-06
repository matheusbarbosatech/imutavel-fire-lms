import os
import uuid
import traceback
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
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

def _get_supabase_client():
    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"❌ Erro ao conectar Supabase: {e}", flush=True)
        return None

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
            try:
                print("📤 [PASSO 3] Iniciando upload para Supabase...", flush=True)
                supabase = _get_supabase_client()
                if not supabase:
                    messages.error(request, 'Erro ao conectar com o servidor. Tente novamente.')
                    return redirect('passo_3')
                uploaded_files = {}
                for key, file in form.cleaned_data.items():
                    try:
                        file_ext = file.name.split('.')[-1].lower()
                        file_name = f"temp/{uuid.uuid4().hex}.{file_ext}"
                        file_content = file.read()
                        print(f"📁 [PASSO 3] Upload: {key} -> {file_name} ({len(file_content)} bytes)", flush=True)
                        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                            path=file_name,
                            file=file_content,
                            file_options={"content-type": file.content_type}
                        )
                        uploaded_files[key] = file_name
                    except Exception as e:
                        print(f"❌ [PASSO 3] Erro no arquivo {key}: {e}", flush=True)
                        messages.error(request, f'Erro ao enviar arquivo: {str(e)}')
                        return redirect('passo_3')
                request.session['uploaded_files'] = uploaded_files
                print(f"✅ [PASSO 3] Sucesso! Arquivos: {list(uploaded_files.keys())}", flush=True)
                return redirect('passo_4')
            except Exception as e:
                print(f"❌ [PASSO 3] ERRO GERAL: {str(e)}", flush=True)
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
            mat = None  # CORREÇÃO CRÍTICA 1: Evita UnboundLocalError no bloco except
            try:
                print("=" * 60, flush=True)
                print("🚀 [PASSO 4] INICIANDO FINALIZAÇÃO", flush=True)
                
                s1_raw = request.session.get('step1', {})
                s1 = {k: _str_to_date(v) for k, v in s1_raw.items()}
                s2 = request.session.get('step2', {})
                
                # CORREÇÃO CRÍTICA 2: Valida CPF repetido ANTES de tentar salvar
                cpf_atual = s1.get('cpf', '')
                if Matricula.objects.filter(cpf=cpf_atual).exists():
                    messages.error(request, 'Este CPF já possui uma matrícula registrada em nosso sistema.')
                    return redirect('passo_1')
                
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
                ua = request.META.get('HTTP_USER_AGENT', 'unknown')[:500]
                
                print(f"👤 [PASSO 4] Criando matrícula para: {s1.get('nome', 'N/A')}", flush=True)
                
                mat = Matricula.objects.create(
                    nome=s1.get('nome', ''),
                    cpf=cpf_atual,
                    rg=s1.get('rg', ''),
                    nascimento=s1.get('nascimento'),
                    email=s2.get('email', ''),
                    telefone=s2.get('telefone', ''),
                    endereco=s2.get('endereco', ''),
                    aceitou_termos=True,
                    ip_registro=ip,
                    user_agent=ua
                )
                print(f"✅ [PASSO 4] Matrícula criada: ID={mat.id}", flush=True)
                
                try:
                    supabase = _get_supabase_client()
                    if supabase:
                        uploaded_files = request.session.get('uploaded_files', {})
                        for key, temp_path in uploaded_files.items():
                            tipo = key.replace('_file', '')
                            try:
                                print(f"📥 [PASSO 4] Processando {tipo}", flush=True)
                                file_content = supabase.storage.from_(settings.SUPABASE_BUCKET).download(temp_path)
                                ext = temp_path.split('.')[-1]
                                final_path = f"docs/{tipo}_{mat.id}.{ext}"
                                
                                supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                                    path=final_path,
                                    file=file_content,
                                    file_options={"content-type": "application/octet-stream", "upsert": "true"}
                                )
                                
                                try:
                                    supabase.storage.from_(settings.SUPABASE_BUCKET).remove([temp_path])
                                except:
                                    pass
                                    
                                Documento.objects.create(
                                    matricula=mat,
                                    tipo=tipo,
                                    arquivo=final_path
                                )
                                print(f"   ✓ Documento {tipo} salvo", flush=True)
                            except Exception as e:
                                print(f"   ⚠ Erro no arquivo {tipo}: {e}", flush=True)
                except Exception as e:
                    print(f"⚠ [PASSO 4] Erro geral no processamento de arquivos: {e}", flush=True)
                
                try:
                    send_mail(
                        subject='Matrícula Recebida - IMUTÁVEL FIRE',
                        message=f'Olá {mat.nome},\n\nSua matrícula foi recebida com sucesso!\nProtocolo: #{mat.id}\n\nEm breve entraremos em contato.\n\nAtenciosamente,\nEquipe IMUTÁVEL FIRE',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[mat.email],
                        fail_silently=True
                    )
                    print("📧 [PASSO 4] E-mail enviado", flush=True)
                except Exception as e:
                    print(f"⚠ [PASSO 4] Falha ao enviar email: {e}", flush=True)
                
                print("🎉 SUCESSO TOTAL, redirecionando!", flush=True)
                _clean_session(request)
                messages.success(request, '✅ Matrícula enviada com sucesso!')
                return redirect('sucesso')
                
            except Exception as e:
                print(f"❌ [PASSO 4] ERRO CRÍTICO: {str(e)}", flush=True)
                print(traceback.format_exc(), flush=True)
                if mat:  # Agora não causará UnboundLocalError
                    _clean_session(request)
                    messages.warning(request, 'Sua inscrição foi salva, mas houve um erro interno de processamento dos arquivos.')
                    return redirect('sucesso')
                messages.error(request, f'Erro ao processar matrícula: {str(e)}')
                return redirect('passo_4')
    else:
        form = Step4Form()
    return render(request, 'core/step.html', {'form': form, 'step': 4, 'title': '✍️ Confirmação e Termos'})

def sucesso(request):
    return render(request, 'core/success.html', {'step': 5})
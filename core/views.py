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

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _date_to_str(obj):
    """Converte date para string (necessário para sessão JSON)"""
    if isinstance(obj, date):
        return obj.isoformat()
    return obj

def _str_to_date(value):
    """Converte string ISO de volta para date"""
    if isinstance(value, str) and len(value) == 10 and value[4] == '-' and value[7] == '-':
        try:
            return date.fromisoformat(value)
        except:
            return value
    return value

def _clean_session(request):
    """Limpa dados temporários da sessão"""
    for k in ['step1', 'step2', 'uploaded_files']:
        if k in request.session:
            del request.session[k]

def _get_supabase_client():
    """Cria cliente Supabase com tratamento de erro"""
    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"❌ Erro ao conectar Supabase: {e}")
        return None

# ============================================================
# PASSO 1: DADOS PESSOAIS
# ============================================================

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
    return render(request, 'core/step.html', {
        'form': form,
        'step': 1,
        'title': '📋 Dados Pessoais'
    })

# ============================================================
# PASSO 2: CONTATO E ENDEREÇO
# ============================================================

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
    return render(request, 'core/step.html', {
        'form': form,
        'step': 2,
        'title': '📍 Contato e Endereço'
    })

# ============================================================
# PASSO 3: UPLOAD DE DOCUMENTOS
# ============================================================

def passo_3(request):
    if 'step2' not in request.session:
        return redirect('passo_2')
    
    if request.method == 'POST':
        form = Step3Form(request.POST, request.FILES)
        if form.is_valid():
            try:
                print("📤 [PASSO 3] Iniciando upload para Supabase...")
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
                        
                        print(f"📁 [PASSO 3] Upload: {key} -> {file_name} ({len(file_content)} bytes)")
                        
                        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                            path=file_name,
                            file=file_content,
                            file_options={"content-type": file.content_type}
                        )
                        uploaded_files[key] = file_name
                    except Exception as e:
                        print(f"❌ [PASSO 3] Erro no arquivo {key}: {e}")
                        messages.error(request, f'Erro ao enviar arquivo: {str(e)}')
                        return redirect('passo_3')
                
                request.session['uploaded_files'] = uploaded_files
                print(f"✅ [PASSO 3] Sucesso! Arquivos: {list(uploaded_files.keys())}")
                return redirect('passo_4')
                
            except Exception as e:
                print(f"❌ [PASSO 3] ERRO GERAL: {str(e)}")
                print(traceback.format_exc())
                messages.error(request, f'Erro ao fazer upload: {str(e)}')
                return redirect('passo_3')
    else:
        form = Step3Form()
    return render(request, 'core/step.html', {
        'form': form,
        'step': 3,
        'title': '📎 Upload de Documentos'
    })

# ============================================================
# PASSO 4: CONFIRMAÇÃO E TERMOS (ULTRA DEFENSIVO)
# ============================================================

def passo_4(request):
    if 'uploaded_files' not in request.session:
        return redirect('passo_3')
    
    if request.method == 'POST':
        form = Step4Form(request.POST)
        if form.is_valid():
            mat = None  # Variável para rastrear se a matrícula foi criada
            
            try:
                print("=" * 60)
                print("🚀 [PASSO 4] INICIANDO FINALIZAÇÃO")
                print("=" * 60)
                
                # Recuperar dados da sessão
                s1_raw = request.session.get('step1', {})
                s1 = {k: _str_to_date(v) for k, v in s1_raw.items()}
                s2 = request.session.get('step2', {})
                
                # IP e User-Agent
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
                ua = request.META.get('HTTP_USER_AGENT', 'unknown')[:500]
                
                print(f"👤 [PASSO 4] Criando matrícula para: {s1.get('nome', 'N/A')}")
                
                # ========================================
                # 1. CRIAR MATRÍCULA (BLOCO CRÍTICO)
                # ========================================
                mat = Matricula.objects.create(
                    nome=s1.get('nome', ''),
                    cpf=s1.get('cpf', ''),
                    rg=s1.get('rg', ''),
                    nascimento=s1.get('nascimento'),
                    email=s2.get('email', ''),
                    telefone=s2.get('telefone', ''),
                    endereco=s2.get('endereco', ''),
                    aceitou_termos=True,
                    ip_registro=ip,
                    user_agent=ua
                )
                print(f"✅ [PASSO 4] Matrícula criada: ID={mat.id}")
                
                # ========================================
                # 2. PROCESSAR ARQUIVOS (NÃO BLOQUEIA)
                # ========================================
                try:
                    supabase = _get_supabase_client()
                    if supabase:
                        uploaded_files = request.session.get('uploaded_files', {})
                        for key, temp_path in uploaded_files.items():
                            tipo = key.replace('_file', '')
                            try:
                                print(f"📥 [PASSO 4] Processando {tipo}")
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
                                print(f"   ✓ Documento {tipo} salvo")
                            except Exception as e:
                                print(f"   ⚠ Erro no arquivo {tipo}: {e}")
                    else:
                        print("⚠ [PASSO 4] Supabase indisponível, pulando arquivos")
                except Exception as e:
                    print(f"⚠ [PASSO 4] Erro geral no processamento de arquivos: {e}")
                
                # ========================================
                # 3. ENVIAR E-MAIL (TOTALMENTE OPCIONAL)
                # ========================================
                try:
                    send_mail(
                        subject='Matrícula Recebida - IMUTÁVEL FIRE',
                        message=f'Olá {mat.nome},\n\nSua matrícula foi recebida com sucesso!\nProtocolo: #{mat.id}\n\nEm breve entraremos em contato.\n\nAtenciosamente,\nEquipe IMUTÁVEL FIRE',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[mat.email],
                        fail_silently=True  # ← NUNCA lança exceção
                    )
                    print("📧 [PASSO 4] E-mail enviado (ou tentativa feita)")
                except Exception as e:
                    print(f"⚠ [PASSO 4] E-mail falhou (não bloqueia): {e}")
                
                # ========================================
                # 4. FINALIZAR E REDIRECIONAR
                # ========================================
                print("=" * 60)
                print("🎉 [PASSO 4] SUCESSO TOTAL!")
                print("=" * 60)
                
                _clean_session(request)
                messages.success(request, '✅ Matrícula enviada com sucesso!')
                return redirect('sucesso')
                
            except Exception as e:
                print("=" * 60)
                print(f"❌ [PASSO 4] ERRO CRÍTICO: {str(e)}")
                print(traceback.format_exc())
                print("=" * 60)
                
                # SE A MATRÍCULA FOI CRIADA, VAI PARA SUCESSO MESMO ASSIM
                if mat:
                    print("⚠ [PASSO 4] Matrícula foi criada, redirecionando para sucesso")
                    _clean_session(request)
                    messages.warning(request, 'Matrícula salva! Houve um pequeno erro no processamento, mas sua inscrição foi registrada.')
                    return redirect('sucesso')
                
                # SE NÃO FOI CRIADA, MOSTRA ERRO E VOLTA
                messages.error(request, f'Erro ao finalizar: {str(e)}')
                return redirect('passo_4')
    else:
        form = Step4Form()
    
    return render(request, 'core/step.html', {
        'form': form,
        'step': 4,
        'title': '✍️ Confirmação e Termos'
    })

# ============================================================
# PÁGINA DE SUCESSO
# ============================================================

def sucesso(request):
    return render(request, 'core/success.html', {'step': 5})
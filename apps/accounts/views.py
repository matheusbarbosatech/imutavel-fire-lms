import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.conf import settings

from .models import StudentDocument, UserBadge, Notification
from .pdf_generators import generate_declaration_pdf
from apps.certificates.models import Certificate


@login_required
def profile_view(request):
    """
    Exibe os dados cadastrais do aluno, permite a edição de informações pessoais,
    upload da foto 3x4, anexo de documentos de matrícula e exibe as medalhas conquistadas.
    """
    user = request.user
    user_badges = UserBadge.objects.filter(user=user).select_related('badge')
    documents = StudentDocument.objects.filter(user=user)

    if request.method == 'POST':
        # 1. Atualização dos Dados Cadastrais / Foto 3x4
        if 'update_profile' in request.POST:
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name = request.POST.get('last_name', user.last_name).strip()
            user.cpf = request.POST.get('cpf', user.cpf).strip()
            user.rg = request.POST.get('rg', user.rg).strip()
            user.cbmerj_registration = request.POST.get('cbmerj_registration', user.cbmerj_registration).strip()
            user.blood_type = request.POST.get('blood_type', user.blood_type).strip()

            if 'photo' in request.FILES:
                user.photo = request.FILES['photo']

            user.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')

        # 2. Upload de Documentos de Matrícula (RG, CPF, ASO, etc.)
        if 'upload_document' in request.POST:
            doc_type = request.POST.get('doc_type')
            file = request.FILES.get('doc_file')
            if doc_type and file:
                StudentDocument.objects.create(user=user, doc_type=doc_type, file=file)
                messages.success(request, 'Documento de matrícula enviado para análise!')
                return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user_badges': user_badges,
        'documents': documents
    })


@login_required
def download_declaration(request, doc_type_code):
    """
    Gera e faz o download instantâneo em PDF das declarações institucionais:
    - MATRICULA: Declaração de Matrícula Ativa
    - FREQUENCIA: Comprovante de Frequência
    - HISTORICO: Histórico Escolar
    - HOMOLOGACAO: Declaração de Aguardando Homologação (30 a 90 dias)
    """
    cert = Certificate.objects.filter(student=request.user).first()
    course_name = cert.course.title if cert else "Treinamento Profissional Regido pela NBR 14608 / CBMERJ"

    rel_path = generate_declaration_pdf(request.user, doc_type_code, course_name=course_name)
    full_path = os.path.join(settings.MEDIA_ROOT, rel_path)

    if os.path.exists(full_path):
        filename_map = {
            'MATRICULA': 'Declaracao_Matricula.pdf',
            'FREQUENCIA': 'Comprovante_Frequencia.pdf',
            'HISTORICO': 'Historico_Escolar.pdf',
            'HOMOLOGACAO': 'Declaracao_Homologacao_30_90_dias.pdf'
        }
        output_filename = filename_map.get(doc_type_code, f"Declaracao_{doc_type_code}.pdf")
        return FileResponse(open(full_path, 'rb'), content_type='application/pdf', filename=output_filename)
    else:
        raise Http404("Documento institucional não localizado.")

    from django.contrib.auth import login
from .models import CustomUser

def register_view(request):
    # Se o usuário já estiver logado, manda ele pro painel
    if request.user.is_authenticated:
        return redirect('courses:student_dashboard')
        
    if request.method == 'POST':
        nome = request.POST.get('first_name')
        email = request.POST.get('email')
        cpf = request.POST.get('cpf')
        senha = request.POST.get('password')
        
        # 1. Verifica se o email já existe
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está em uso. Tente recuperar a senha.')
            return redirect('accounts:register')
            
        try:
            # 2. Cria o novo usuário
            user = CustomUser(
                email=email,
                first_name=nome,
                cpf=cpf,
                role='STUDENT' # Define automaticamente como ALUNO
            )
            
            # Se o seu CustomUser usar o padrão do Django, ele precisa do 'username'
            if hasattr(user, 'username'):
                user.username = email 
                
            user.set_password(senha) # Criptografa a senha com segurança
            user.save()
            
            # 3. Faz o login automático e manda pro painel
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso! Bem-vindo(a) ao Imutável Fire.')
            return redirect('courses:student_dashboard')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar conta. Verifique os dados e tente novamente.')
            return redirect('accounts:register')
            
    return render(request, 'accounts/register.html')

from django.http import HttpResponse

def gerar_admin_secreto(request):
    from .models import CustomUser
    
    email_admin = 'admin@imutavel.com'
    senha_admin = 'SenhaForte2026!'
    
    try:
        # Se o admin já existir, ele só atualiza a senha e força as permissões
        admin = CustomUser.objects.get(email=email_admin)
        admin.set_password(senha_admin)
        admin.is_staff = True
        admin.is_superuser = True
        admin.role = 'ADMIN'
        admin.save()
        return HttpResponse(f"✅ Admin RECUPERADO! Acesse o painel com:<br>Email: {email_admin}<br>Senha: {senha_admin}")
        
    except CustomUser.DoesNotExist:
        # Se não existir, ele cria do zero com força total
        admin = CustomUser(
            email=email_admin,
            first_name="Diretoria",
            cpf="000.000.000-00",
            role='ADMIN',
            is_staff=True,
            is_superuser=True
        )
        if hasattr(admin, 'username'):
            admin.username = email_admin
            
        admin.set_password(senha_admin)
        admin.save()
        return HttpResponse(f"🚀 NOVO Admin CRIADO COM SUCESSO! Acesse o painel com:<br>Email: {email_admin}<br>Senha: {senha_admin}")

    def matricular_admin_em_tudo(request):
    from apps.accounts.models import CustomUser
    from apps.courses.models import Course, Enrollment
    from django.http import HttpResponse

    try:
        # Pega o seu usuário admin
        admin = CustomUser.objects.get(email='admin@imutavel.com')
        
        # Pega todos os cursos cadastrados no sistema
        cursos = Course.objects.all()
        
        if not cursos.exists():
            return HttpResponse("⚠️ Nenhum curso encontrado no banco de dados. Crie os cursos primeiro no painel /admin/!")

        matriculados = 0
        for curso in cursos:
            # get_or_create garante que ele não vai duplicar a matrícula se já existir
            matricula, created = Enrollment.objects.get_or_create(
                student=admin,
                course=curso
            )
            if created:
                matriculados += 1
        
        return HttpResponse(f"✅ SUCESSO! O usuário {admin.email} foi matriculado em {matriculados} novos cursos.<br>Vá para o painel /courses/ e veja seus treinamentos!")
        
    except CustomUser.DoesNotExist:
        return HttpResponse("❌ Erro: O usuário admin@imutavel.com não foi encontrado. Rode a chave-mestra primeiro.")
    except Exception as e:
        return HttpResponse(f"❌ Erro inesperado: {str(e)}")
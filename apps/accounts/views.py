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
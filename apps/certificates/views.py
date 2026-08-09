import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.conf import settings
from .models import Certificate
from .card_generator import generate_pvc_card_pdf
from .utils import generate_certificate_pdf


@login_required
def my_certificates_view(request):
    """Lista de certificados obtidos pelo aluno."""
    certificates = Certificate.objects.filter(student=request.user)
    return render(request, 'certificates/my_certificates.html', {'certificates': certificates})


def verify_certificate_view(request, code):
    """Validação pública do certificado via código de autenticidade."""
    certificate = get_object_or_404(Certificate, code=code)
    return render(request, 'certificates/verify_certificate.html', {'certificate': certificate})


@login_required
def download_pvc_card_view(request, certificate_id):
    """Gera e faz o download da Credencial Operacional em PVC (Bombeiro Civil)."""
    certificate = get_object_or_404(Certificate, id=certificate_id, student=request.user)
    rel_path = generate_pvc_card_pdf(request.user, certificate, base_url=request.build_absolute_uri('/')[:-1])
    full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
    if os.path.exists(full_path):
        return FileResponse(open(full_path, 'rb'), content_type='application/pdf', filename=f"carteirinha_{certificate.code}.pdf")
    raise Http404("Arquivo da carteirinha PVC não encontrado.")


@login_required
def download_certificate_pdf_view(request, certificate_id):
    """Gera e faz o download do Certificado Oficial em PDF."""
    certificate = get_object_or_404(Certificate, id=certificate_id, student=request.user)
    if not certificate.pdf_file or not os.path.exists(certificate.pdf_file.path):
        generate_certificate_pdf(certificate, base_url=request.build_absolute_uri('/')[:-1])
    
    if certificate.pdf_file and os.path.exists(certificate.pdf_file.path):
        return FileResponse(open(certificate.pdf_file.path, 'rb'), content_type='application/pdf', filename=f"certificado_{certificate.code}.pdf")
    raise Http404("Arquivo de certificado não encontrado.")
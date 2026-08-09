from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Certificate


@login_required
def my_certificates_view(request):
    """Lista de certificados obtidos pelo aluno."""
    certificates = Certificate.objects.filter(student=request.user)
    return render(request, 'certificates/my_certificates.html', {'certificates': certificates})


def verify_certificate_view(request, code):
    """Validação pública do certificado via código de autenticidade."""
    certificate = get_object_or_404(Certificate, code=code)
    return render(request, 'certificates/verify_certificate.html', {'certificate': certificate})
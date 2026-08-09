import logging
import mercadopago
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from apps.accounts.models import CustomUser
from apps.courses.models import Course, Enrollment
from .decorators import admin_required

logger = logging.getLogger(__name__)

def get_mp_sdk():
    """Retorna o SDK do Mercado Pago inicializado de forma segura."""
    token = getattr(settings, 'MP_ACCESS_TOKEN', '') or ''
    if not token:
        logger.warning("MP_ACCESS_TOKEN não configurado em settings.")
    return mercadopago.SDK(token)


def landing_page_view(request):
    """Landing Page pública do sistema na raiz (/)."""
    try:
        cursos_disponiveis = Course.objects.all()[:3]
    except Exception as e:
        logger.error(f"Erro ao carregar cursos na Landing Page: {e}")
        cursos_disponiveis = []

    context = {'cursos': cursos_disponiveis}
    return render(request, 'management/landing_page.html', context)


@admin_required
def dashboard_view(request):
    """Painel de BI e Métricas do Gestor."""
    try:
        total_alunos = CustomUser.objects.filter(role='STUDENT').count()
        total_cursos = Course.objects.count()
        total_matriculas = Enrollment.objects.count()
    except Exception as e:
        logger.error(f"Erro ao carregar métricas da dashboard: {e}")
        total_alunos = total_cursos = total_matriculas = 0

    context = {
        'total_alunos': total_alunos,
        'total_cursos': total_cursos,
        'total_matriculas': total_matriculas,
    }
    try:
        return render(request, 'management/dashboard.html', context)
    except Exception as e:
        logger.error(f"Erro ao renderizar template da dashboard: {e}")
        return redirect('courses:dashboard')


@admin_required
def enrollment_list_view(request):
    """Listagem otimizada de matrículas."""
    try:
        matriculas = Enrollment.objects.all().select_related('student', 'course')
        return render(request, 'management/enrollment_list.html', {'matriculas': matriculas})
    except Exception as e:
        logger.error(f"Erro ao buscar matrículas: {e}")
        return redirect('courses:dashboard')


@admin_required
def enrollment_action_view(request, enrollment_id, action):
    """Ações rápidas de alteração de status de matrícula."""
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        if action == 'aprovar':
            enrollment.is_active = True
            enrollment.save()
        elif action == 'bloquear':
            enrollment.is_active = False
            enrollment.save()
    except Enrollment.DoesNotExist:
        logger.warning(f"Matrícula {enrollment_id} não encontrada.")
    except Exception as e:
        logger.error(f"Erro ao alterar status da matrícula {enrollment_id}: {e}")

    return redirect('management:enrollment_list')


@admin_required
def financial_list_view(request):
    """Visão geral do financeiro."""
    return render(request, 'management/financial_list.html')


@admin_required
def register_payment_view(request, payment_id):
    """Baixa de pagamentos manuais."""
    return redirect('management:financial_list')


def criar_pagamento_mercadopago(request):
    """Gera a preferência de pagamento no Mercado Pago e redireciona o aluno."""
    if request.method == 'POST':
        nome_curso = request.POST.get('curso_nome', 'Curso Profissional Bombeiro Civil')
        preco = request.POST.get('preco', '750.00')
        email_aluno = request.POST.get('email', '').strip()

        if not email_aluno:
            return redirect('management:landing_page')

        try:
            preco_float = float(preco)
            sdk = get_mp_sdk()

            preference_data = {
                "items": [
                    {
                        "title": str(nome_curso),
                        "quantity": 1,
                        "unit_price": preco_float,
                        "currency_id": "BRL"
                    }
                ],
                "payer": {
                    "email": str(email_aluno)
                },
                "back_urls": {
                    "success": "https://sistema-matricula-fmp9.onrender.com/courses/dashboard/?pagamento=sucesso",
                    "failure": "https://sistema-matricula-fmp9.onrender.com/?pagamento=falha",
                    "pending": "https://sistema-matricula-fmp9.onrender.com/?pagamento=pendente"
                },
                "auto_return": "approved",
                "notification_url": "https://sistema-matricula-fmp9.onrender.com/pagamentos/webhook/"
            }

            preference_response = sdk.preference().create(preference_data)
            response_data = preference_response.get("response", {})
            init_point = response_data.get("init_point") or response_data.get("sandbox_init_point")

            if init_point:
                return redirect(init_point)
            
            logger.error(f"Mercado Pago não retornou init_point: {response_data}")

        except Exception as e:
            logger.error(f"Exceção ao comunicar com Mercado Pago: {e}")

    return redirect('management:landing_page')


@csrf_exempt
def mercadopago_webhook(request):
    """Webhook silencioso para aprovação de pagamento e liberação de acesso."""
    if request.method == 'POST':
        topic = request.GET.get('topic') or request.POST.get('type') or request.GET.get('type')
        payment_id = request.GET.get('id') or request.POST.get('data.id') or request.GET.get('data.id')

        if (topic in ['payment', 'merchant_order']) and payment_id:
            try:
                sdk = get_mp_sdk()
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info.get("response", payment_info)

                if payment and payment.get("status") == "approved":
                    email_comprador = payment.get("payer", {}).get("email")

                    if email_comprador:
                        with transaction.atomic():
                            user, created = CustomUser.objects.get_or_create(
                                email=email_comprador,
                                defaults={
                                    'first_name': email_comprador.split('@')[0],
                                    'role': 'STUDENT',
                                    'username': email_comprador
                                }
                            )
                            if created:
                                user.set_password('MudeSuaSenha123')
                                user.save()

                            cursos = Course.objects.all()
                            for curso in cursos:
                                Enrollment.objects.get_or_create(
                                    student=user, 
                                    course=curso, 
                                    defaults={'is_active': True}
                                )
                            logger.info(f"Matrícula ativada automaticamente: {email_comprador}")

            except Exception as e:
                logger.error(f"Erro no processamento do webhook Mercado Pago: {e}")

        return HttpResponse(status=200)

    return HttpResponse(status=200)
import mercadopago
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from apps.accounts.models import CustomUser
from apps.courses.models import Course, Enrollment

def get_mp_sdk():
    """Inicializa o SDK do Mercado Pago dinamicamente com o token das configurações."""
    token = getattr(settings, 'MP_ACCESS_TOKEN', None) or 'APP_USR-seu-token-aqui'
    return mercadopago.SDK(token)

def landing_page_view(request):
    """Landing Page pública na raiz (/)"""
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            return redirect('management:dashboard')
        return redirect('courses:course_list')  # Redirecionamento seguro para catálogo/dashboard do aluno
        
    cursos_disponiveis = Course.objects.all()[:3]
    context = {
        'cursos': cursos_disponiveis,
    }
    return render(request, 'management/landing_page.html', context)


@login_required
def dashboard_view(request):
    """Painel Administrativo / Gestor (BI e Métricas)"""
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:course_list')
        
    total_alunos = CustomUser.objects.filter(role='STUDENT').count()
    total_cursos = Course.objects.count()
    total_matriculas = Enrollment.objects.count()
    
    context = {
        'total_alunos': total_alunos,
        'total_cursos': total_cursos,
        'total_matriculas': total_matriculas,
    }
    return render(request, 'management/dashboard.html', context)


@login_required
def enrollment_list_view(request):
    """Lista de matrículas para gestão"""
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:course_list')
    
    matriculas = Enrollment.objects.all().select_related('student', 'course')
    context = {'matriculas': matriculas}
    return render(request, 'management/enrollment_list.html', context)


@login_required
def enrollment_action_view(request, enrollment_id, action):
    """Ações de aprovar ou bloquear matrículas"""
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:course_list')
        
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        if action == 'aprovar':
            enrollment.is_active = True
            enrollment.save()
        elif action == 'bloquear':
            enrollment.is_active = False
            enrollment.save()
    except Enrollment.DoesNotExist:
        pass
        
    return redirect('management:enrollment_list')


@login_required
def financial_list_view(request):
    """Painel financeiro do gestor"""
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:course_list')
    return render(request, 'management/financial_list.html')


@login_required
def register_payment_view(request, payment_id):
    """Baixa de pagamentos manuais"""
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:course_list')
    return redirect('management:financial_list')


def criar_pagamento_mercadopago(request):
    """Gera a preferência de pagamento no Mercado Pago e redireciona o aluno"""
    if request.method == 'POST':
        nome_curso = request.POST.get('curso_nome', 'Imutável Fire - Acesso Completo')
        preco = float(request.POST.get('preco', 97.00))
        email_aluno = request.POST.get('email', 'aluno@email.com')

        preference_data = {
            "items": [
                {
                    "title": nome_curso,
                    "quantity": 1,
                    "unit_price": preco,
                    "currency_id": "BRL"
                }
            ],
            "payer": {
                "email": email_aluno
            },
            "back_urls": {
                "success": "https://sistema-matricula-fmp9.onrender.com/courses/?pagamento=sucesso",
                "failure": "https://sistema-matricula-fmp9.onrender.com/?pagamento=falha",
                "pending": "https://sistema-matricula-fmp9.onrender.com/?pagamento=pendente"
            },
            "auto_return": "approved",
            "notification_url": "https://sistema-matricula-fmp9.onrender.com/pagamentos/webhook/"
        }

        try:
            sdk = get_mp_sdk()
            preference_response = sdk.preference().create(preference_data)
            
            # Tratamento resiliente para diferentes versões da SDK do Mercado Pago
            preference = preference_response.get("response", preference_response)
            
            init_point = preference.get("init_point")
            if init_point:
                return redirect(init_point)
            else:
                print(f"Mercado Pago Retornou: {preference_response}")
        except Exception as e:
            print(f"Erro ao gerar pagamento MP: {e}")
            
    return redirect('management:landing_page')


@csrf_exempt
def mercadopago_webhook(request):
    """Recebe a notificação silenciosa do Mercado Pago quando o pagamento é aprovado"""
    if request.method == 'POST':
        topic = request.GET.get('topic') or request.POST.get('type') or request.GET.get('type')
        payment_id = request.GET.get('id') or request.POST.get('data.id') or request.GET.get('data.id')

        if (topic == 'payment' or topic == 'merchant_order') and payment_id:
            try:
                sdk = get_mp_sdk()
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info.get("response", payment_info)
                
                if payment and payment.get("status") == "approved":
                    email_comprador = payment.get("payer", {}).get("email")
                    
                    if email_comprador:
                        user, created = CustomUser.objects.get_or_create(
                            email=email_comprador,
                            defaults={
                                'first_name': 'Aluno SaaS',
                                'role': 'STUDENT',
                                'username': email_comprador
                            }
                        )
                        if created:
                            user.set_password('MudeSuaSenha123')
                            user.save()
                        
                        cursos = Course.objects.all()
                        for curso in cursos:
                            Enrollment.objects.get_or_create(student=user, course=curso)
                            
            except Exception as e:
                print(f"Erro no processamento do webhook: {e}")
                
        return HttpResponse(status=200)
        
    return HttpResponse(status=200)  # Retorna 200 para evitar retentativas desnecessárias do MP em Webhooks de teste
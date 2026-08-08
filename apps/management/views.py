import mercadopago
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from apps.accounts.models import CustomUser
from apps.courses.models import Course, Enrollment

# Inicializa o SDK do Mercado Pago com a chave de API (Lendo do settings ou variável de ambiente)
MP_TOKEN = getattr(settings, 'MP_ACCESS_TOKEN', 'APP_USR-seu-token-aqui')
sdk = mercadopago.SDK(MP_TOKEN)

def landing_page_view(request):
    """Cenário A: A Landing Page oficial na raiz do site (/)"""
    # Se o usuário já estiver logado, podemos redirecionar direto para o painel dele
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN':
            return redirect('management:dashboard')
        return redirect('courses:student_dashboard')
        
    # Busca alguns cursos para exibir na vitrine da Landing Page
    cursos_disponiveis = Course.objects.all()[:3]
    
    context = {
        'cursos': cursos_disponiveis,
    }
    return render(request, 'management/landing_page.html', context)


@login_required
def dashboard_view(request):
    """Painel Administrativo / Gestor (BI e Métricas)"""
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:student_dashboard')
        
    total_alunos = CustomUser.objects.filter(role='STUDENT').count()
    total_cursos = Course.objects.count()
    total_matriculas = Enrollment.objects.count()
    
    context = {
        'total_alunos': total_alunos,
        'total_cursos': total_cursos,
        'total_matriculas': total_matriculas,
    }
    return render(request, 'management/dashboard.html', context)


def criar_pagamento_mercadopago(request):
    """Gera a preferência de pagamento no Mercado Pago e redireciona o aluno"""
    if request.method == 'POST':
        nome_curso = request.POST.get('curso_nome', 'Imutável Fire - Acesso Completo')
        preco = float(request.POST.get('preco', 97.00))
        email_aluno = request.POST.get('email', 'aluno@email.com')

        # Dados estruturados para o Checkout do Mercado Pago
        preference_data = {
            "items": [
                {
                    "title": nome_curso,
                    "quantity": 1,
                    "unit_price": preco
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
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response.get("response")
            
            if preference and "init_point" in preference:
                # Redireciona para o link oficial de pagamento do Mercado Pago
                return redirect(preference["init_point"])
        except Exception as e:
            print(f"Erro ao gerar pagamento MP: {e}")
            
    return redirect('management:landing_page')


@csrf_exempt
def mercadopago_webhook(request):
    """Recebe a notificação silenciosa do Mercado Pago quando o pagamento é aprovado"""
    if request.method == 'POST':
        topic = request.GET.get('topic') or request.POST.get('type')
        payment_id = request.GET.get('id') or request.POST.get('data_id')

        if topic == 'payment' and payment_id:
            try:
                # Consulta os detalhes do pagamento diretamente na API do Mercado Pago
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info.get("response")
                
                if payment and payment.get("status") == "approved":
                    email_comprador = payment.get("payer", {}).get("email")
                    
                    # 1. Verifica se o usuário já existe, se não, cria uma conta provisória
                    user, created = CustomUser.objects.get_or_create(
                        email=email_comprador,
                        defaults={
                            'first_name': 'Aluno SaaS',
                            'role': 'STUDENT',
                            'username': email_comprador
                        }
                    )
                    if created:
                        user.set_password('MudeSuaSenha123') # Senha temporária enviada por email depois
                        user.save()
                    
                    # 2. Matricula o usuário em todos os cursos ativos (ou no curso comprado)
                    cursos = Course.objects.all()
                    for curso in cursos:
                        Enrollment.objects.get_or_create(student=user, course=curso)
                        
            except Exception as e:
                print(f"Erro no processamento do webhook: {e}")
                
        return HttpResponse(status=200)
        
    return HttpResponse(status=400)
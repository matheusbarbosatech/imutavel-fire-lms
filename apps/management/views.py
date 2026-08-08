from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from apps.accounts.models import CustomUser
from apps.courses.models import Course, Enrollment

def landing_page_view(request):
    """
    Landing Page pública na raiz (/)
    Exibe a Landing Page para TODOS (anônimos e logados), sem redirecionamento forçado.
    """
    try:
        cursos_disponiveis = Course.objects.all()[:3]
    except Exception:
        cursos_disponiveis = []
    
    context = {
        'cursos': cursos_disponiveis,
    }
    return render(request, 'management/landing_page.html', context)


@login_required
def dashboard_view(request):
    """Painel Administrativo / Gestor (Com fallback total para não dar 500)"""
    if getattr(request.user, 'role', '') != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:dashboard')
        
    try:
        total_alunos = CustomUser.objects.filter(role='STUDENT').count()
        total_cursos = Course.objects.count()
        total_matriculas = Enrollment.objects.count()
    except Exception:
        total_alunos = total_cursos = total_matriculas = 0
    
    context = {
        'total_alunos': total_alunos,
        'total_cursos': total_cursos,
        'total_matriculas': total_matriculas,
    }
    try:
        return render(request, 'management/dashboard.html', context)
    except Exception as e:
        print(f"Erro ao renderizar management/dashboard.html: {e}")
        return redirect('courses:dashboard')


@login_required
def enrollment_list_view(request):
    if getattr(request.user, 'role', '') != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:dashboard')
    try:
        matriculas = Enrollment.objects.all().select_related('student', 'course')
        return render(request, 'management/enrollment_list.html', {'matriculas': matriculas})
    except Exception:
        return redirect('courses:dashboard')


@login_required
def enrollment_action_view(request, enrollment_id, action):
    if getattr(request.user, 'role', '') != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:dashboard')
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        if action == 'aprovar':
            enrollment.is_active = True
            enrollment.save()
        elif action == 'bloquear':
            enrollment.is_active = False
            enrollment.save()
    except Exception:
        pass
    return redirect('management:enrollment_list')


@login_required
def financial_list_view(request):
    if getattr(request.user, 'role', '') != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:dashboard')
    try:
        return render(request, 'management/financial_list.html')
    except Exception:
        return redirect('courses:dashboard')


@login_required
def register_payment_view(request, payment_id):
    if getattr(request.user, 'role', '') != 'ADMIN' and not request.user.is_superuser:
        return redirect('courses:dashboard')
    return redirect('management:financial_list')


def criar_pagamento_mercadopago(request):
    """Gera a preferência no Mercado Pago"""
    if request.method == 'POST':
        nome_curso = request.POST.get('curso_nome', 'Imutável Fire - Acesso Completo')
        preco = float(request.POST.get('preco', 97.00))
        email_aluno = request.POST.get('email', 'aluno@email.com')

        try:
            import mercadopago
            token = getattr(settings, 'MP_ACCESS_TOKEN', None) or 'APP_USR-seu-token-aqui'
            sdk = mercadopago.SDK(token)

            preference_data = {
                "items": [{"title": nome_curso, "quantity": 1, "unit_price": preco, "currency_id": "BRL"}],
                "payer": {"email": email_aluno},
                "back_urls": {
                    "success": "https://sistema-matricula-fmp9.onrender.com/courses/dashboard/?pagamento=sucesso",
                    "failure": "https://sistema-matricula-fmp9.onrender.com/?pagamento=falha",
                    "pending": "https://sistema-matricula-fmp9.onrender.com/?pagamento=pendente"
                },
                "auto_return": "approved",
                "notification_url": "https://sistema-matricula-fmp9.onrender.com/pagamentos/webhook/"
            }

            preference_response = sdk.preference().create(preference_data)
            preference = preference_response.get("response", preference_response)
            init_point = preference.get("init_point")
            if init_point:
                return redirect(init_point)
        except Exception as e:
            print(f"Erro ao gerar pagamento Mercado Pago: {e}")

    return redirect('management:landing_page')


@csrf_exempt
def mercadopago_webhook(request):
    return HttpResponse(status=200)
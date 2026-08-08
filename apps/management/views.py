from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import Payment
from apps.courses.models import Enrollment
from apps.accounts.models import CustomUser

# --- DECORATOR PARA RESTRINGIR ACESSO ---
def is_manager(user):
    return user.is_authenticated and (user.role in ['ADMIN', 'MANAGER'] or user.is_superuser)

# --- 1. PAINEL DE BI (DASHBOARD) ---
@login_required
@user_passes_test(is_manager, login_url='/courses/dashboard/')
def dashboard_view(request):
    now = timezone.now()
    
    # KPIs Financeiros
    revenue_month = Payment.objects.filter(
        status='PAID', payment_date__month=now.month, payment_date__year=now.year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pending_revenue = Payment.objects.filter(
        status__in=['PENDING', 'OVERDUE']
    ).aggregate(total=Sum('amount'))['total'] or 0

    # KPIs Operacionais
    active_enrollments = Enrollment.objects.filter(is_active=True).count()
    suspended_enrollments = Enrollment.objects.filter(is_active=False).count()
    
    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:5]

    context = {
        'revenue_month': revenue_month,
        'pending_revenue': pending_revenue,
        'active_enrollments': active_enrollments,
        'suspended_enrollments': suspended_enrollments,
        'recent_enrollments': recent_enrollments,
    }
    return render(request, 'management/dashboard.html', context)

# --- 2. GESTÃO DE MATRÍCULAS ---
@login_required
@user_passes_test(is_manager)
def enrollment_list_view(request):
    enrollments = Enrollment.objects.select_related('student', 'course').prefetch_related('student__enrollment_documents').order_by('-enrolled_at')
    return render(request, 'management/enrollment_list.html', {'enrollments': enrollments})

@login_required
@user_passes_test(is_manager)
def enrollment_action_view(request, enrollment_id, action):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    if action == 'block':
        enrollment.is_active = False
        messages.warning(request, f'Acesso bloqueado para {enrollment.student.get_full_name()}.')
    elif action == 'unblock':
        enrollment.is_active = True
        messages.success(request, f'Acesso liberado para {enrollment.student.get_full_name()}.')
    enrollment.save()
    return redirect('management:enrollment_list')

# --- 3. GESTÃO FINANCEIRA ---
@login_required
@user_passes_test(is_manager)
def financial_list_view(request):
    # Atualiza status Atrasado automaticamente antes de exibir
    Payment.objects.filter(status='PENDING', due_date__lt=timezone.now().date()).update(status='OVERDUE')
    
    payments = Payment.objects.select_related('enrollment__student', 'enrollment__course').order_by('due_date')
    return render(request, 'management/financial_list.html', {'payments': payments})

@login_required
@user_passes_test(is_manager)
def register_payment_view(request, payment_id):
    """ Baixa manual de pagamento """
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        payment.status = 'PAID'
        payment.payment_date = timezone.now().date()
        payment.save()
        
        # Libera a matrícula caso estivesse bloqueada
        payment.enrollment.is_active = True
        payment.enrollment.save()
        
        messages.success(request, 'Pagamento liquidado e matrícula liberada com sucesso.')
    return redirect('management:financial_list')
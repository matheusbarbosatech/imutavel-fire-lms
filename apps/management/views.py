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


import csv
from apps.accounts.models import StudentDocument
from .models import Payment

@admin_required
def document_verification_list_view(request):
    """Listagem de documentos de matrícula enviados pelos alunos para conferência da secretaria."""
    documents = StudentDocument.objects.all().select_related('user').order_by('-uploaded_at')
    return render(request, 'management/document_list.html', {'documents': documents})


@admin_required
def document_verify_action_view(request, doc_id, action):
    """Aprova ou rejeita a verificação de um documento de aluno."""
    try:
        doc = StudentDocument.objects.get(id=doc_id)
        if action == 'aprovar':
            doc.is_verified = True
            doc.save()
        elif action == 'rejeitar':
            doc.is_verified = False
            doc.save()
    except StudentDocument.DoesNotExist:
        logger.warning(f"Documento {doc_id} não encontrado.")
    return redirect('management:document_list')


@admin_required
def export_enrollments_csv_view(request):
    """Exporta a lista completa de matrículas em formato CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="matriculas_imutavel.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['ID', 'Aluno', 'E-mail', 'CPF', 'Curso', 'Data Matrícula', 'Status'])

    enrollments = Enrollment.objects.all().select_related('student', 'course')
    for e in enrollments:
        writer.writerow([
            e.id,
            e.student.get_full_name() or e.student.username,
            e.student.email,
            getattr(e.student, 'cpf', ''),
            e.course.title,
            e.enrolled_at.strftime('%d/%m/%Y %H:%M'),
            'Ativa' if e.is_active else 'Inativa'
        ])

    return response


@admin_required
def export_payments_csv_view(request):
    """Exporta o relatório financeiro em formato CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="financeiro_imutavel.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow(['ID Fatura', 'Aluno', 'Valor (R$)', 'Vencimento', 'Data Pagamento', 'Método', 'Status'])

    payments = Payment.objects.all().select_related('enrollment__student')
    for p in payments:
        writer.writerow([
            p.id,
            p.enrollment.student.get_full_name() or p.enrollment.student.username,
            str(p.amount),
            p.due_date.strftime('%d/%m/%Y') if p.due_date else '',
            p.payment_date.strftime('%d/%m/%Y') if p.payment_date else '',
            p.get_payment_method_display(),
            p.get_status_display()
        ])

    return response


from apps.courses.models import Module, Lesson, Quiz, Question, Answer
from django.shortcuts import get_object_or_404
from django.contrib import messages

@admin_required
def course_manage_list_view(request):
    """Painel de Gestão de Conteúdo: Exibe todos os cursos, módulos e aulas para edição."""
    courses = Course.objects.all().prefetch_related('modules__lessons')
    return render(request, 'management/course_manage_list.html', {'courses': courses})


@admin_required
def create_course_view(request):
    """Cria um novo curso na plataforma."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        if title:
            course = Course.objects.create(title=title, description=description, is_active=True)
            messages.success(request, f'Curso "{course.title}" criado com sucesso!')
            return redirect('management:course_manage_list')
        else:
            messages.error(request, 'O título do curso é obrigatório.')
    return redirect('management:course_manage_list')


@admin_required
def create_module_view(request, course_id):
    """Cria um novo módulo dentro de um curso."""
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        order = request.POST.get('order', '1')
        try:
            order_int = int(order)
        except ValueError:
            order_int = 1

        if title:
            module = Module.objects.create(course=course, title=title, order=order_int)
            messages.success(request, f'Módulo "{module.title}" adicionado ao curso!')
        else:
            messages.error(request, 'O título do módulo é obrigatório.')
    return redirect('management:course_manage_list')


@admin_required
def create_lesson_view(request):
    """Formulário para cadastro de uma nova aula com vídeo, texto e anexo."""
    if request.method == 'POST':
        module_id = request.POST.get('module_id')
        title = request.POST.get('title', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        content = request.POST.get('content', '').strip()
        order = request.POST.get('order', '1')
        attachment = request.FILES.get('attachment')

        try:
            order_int = int(order)
        except ValueError:
            order_int = 1

        if module_id and title:
            module = get_object_or_404(Module, id=module_id)
            lesson = Lesson.objects.create(
                module=module,
                title=title,
                video_url=video_url,
                content=content,
                attachment=attachment,
                order=order_int
            )
            messages.success(request, f'Aula "{lesson.title}" cadastrada com sucesso!')
            return redirect('management:course_manage_list')
        else:
            messages.error(request, 'Selecione o módulo e preencha o título da aula.')

    modules = Module.objects.all().select_related('course')
    return render(request, 'management/lesson_form.html', {'modules': modules, 'lesson': None})


@admin_required
def edit_lesson_view(request, lesson_id):
    """Edição de uma aula existente."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        content = request.POST.get('content', '').strip()
        order = request.POST.get('order', '1')
        attachment = request.FILES.get('attachment')

        try:
            order_int = int(order)
        except ValueError:
            order_int = 1

        if title:
            lesson.title = title
            lesson.video_url = video_url
            lesson.content = content
            lesson.order = order_int
            if attachment:
                lesson.attachment = attachment
            lesson.save()
            messages.success(request, f'Aula "{lesson.title}" atualizada com sucesso!')
            return redirect('management:course_manage_list')
        else:
            messages.error(request, 'O título da aula é obrigatório.')

    modules = Module.objects.all().select_related('course')
    return render(request, 'management/lesson_form.html', {'modules': modules, 'lesson': lesson})


@admin_required
def create_quiz_view(request, lesson_id):
    """Criação de avaliação (quiz) e perguntas para uma aula."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        min_score = request.POST.get('min_score', '70')
        q1_text = request.POST.get('q1_text', '').strip()
        q1_a1 = request.POST.get('q1_a1', '').strip()
        q1_a2 = request.POST.get('q1_a2', '').strip()
        q1_correct = request.POST.get('q1_correct', '1')

        try:
            min_score_int = int(min_score)
        except ValueError:
            min_score_int = 70

        if title:
            quiz, _ = Quiz.objects.get_or_create(
                lesson=lesson,
                defaults={'title': title, 'min_score': min_score_int}
            )
            quiz.title = title
            quiz.min_score = min_score_int
            quiz.save()

            if q1_text and q1_a1 and q1_a2:
                q1 = Question.objects.create(quiz=quiz, text=q1_text)
                Answer.objects.create(question=q1, text=q1_a1, is_correct=(q1_correct == '1'))
                Answer.objects.create(question=q1, text=q1_a2, is_correct=(q1_correct == '2'))

            messages.success(request, f'Avaliação "{quiz.title}" cadastrada para a aula!')
            return redirect('management:course_manage_list')

    existing_quiz = Quiz.objects.filter(lesson=lesson).first()
    return render(request, 'management/quiz_form.html', {'lesson': lesson, 'quiz': existing_quiz})
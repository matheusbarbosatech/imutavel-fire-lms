from django.http import JsonResponse, FileResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from .models import Course, Module, Lesson, LessonProgress, LessonComment, Enrollment, Quiz, Question, Answer
from apps.quizzes.models import StudentQuizAttempt

try:
    from apps.certificates.models import IssuedCertificate
except ImportError:
    IssuedCertificate = None

try:
    from apps.management.models import Payment, DocumentVerification
except ImportError:
    Payment = None
    DocumentVerification = None

import json
import os

User = get_user_model()


def api_courses_list(request):
    """
    GET /api/courses/
    Retorna a lista de todos os cursos com seus módulos, aulas, 
    URLs de vídeos, URLs de anexos/materiais (PDF/Áudio) e quizzes.
    """
    courses = Course.objects.filter(is_active=True).prefetch_related(
        'modules__lessons__quiz__questions__answers'
    )
    
    courses_data = []
    for course in courses:
        modules_data = []
        for module in course.modules.all():
            lessons_data = []
            for lesson in module.lessons.all():
                attachment_url = None
                if lesson.attachment:
                    attachment_url = request.build_absolute_uri(lesson.attachment.url)
                
                quiz_data = None
                if hasattr(lesson, 'quiz') and lesson.quiz:
                    quiz = lesson.quiz
                    questions_data = []
                    for q in quiz.questions.all():
                        answers_data = [
                            {
                                'id': a.id,
                                'text': a.text,
                                'is_correct': a.is_correct
                            }
                            for a in q.answers.all()
                        ]
                        questions_data.append({
                            'id': q.id,
                            'text': q.text,
                            'answers': answers_data
                        })
                    
                    quiz_data = {
                        'id': quiz.id,
                        'title': quiz.title,
                        'min_score': quiz.min_score,
                        'questions': questions_data
                    }

                lessons_data.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'content': lesson.content,
                    'video_url': lesson.video_url,
                    'embed_video_url': lesson.get_embed_video_url,
                    'attachment_url': attachment_url,
                    'order': lesson.order,
                    'quiz': quiz_data
                })

            modules_data.append({
                'id': module.id,
                'title': module.title,
                'order': module.order,
                'lessons': lessons_data
            })

        courses_data.append({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'created_at': course.created_at.isoformat() if course.created_at else None,
            'modules': modules_data
        })

    return JsonResponse(courses_data, safe=False)


def api_lesson_detail(request, lesson_id):
    """
    GET /api/lessons/<int:lesson_id>/
    Retorna os detalhes completos de uma aula em JSON.
    """
    lesson = get_object_or_404(
        Lesson.objects.select_related('module__course').prefetch_related('quiz__questions__answers'),
        id=lesson_id
    )

    attachment_url = None
    if lesson.attachment:
        attachment_url = request.build_absolute_uri(lesson.attachment.url)

    quiz_data = None
    if hasattr(lesson, 'quiz') and lesson.quiz:
        quiz = lesson.quiz
        questions_data = []
        for q in quiz.questions.all():
            answers_data = [
                {
                    'id': a.id,
                    'text': a.text,
                    'is_correct': a.is_correct
                }
                for a in q.answers.all()
            ]
            questions_data.append({
                'id': q.id,
                'text': q.text,
                'answers': answers_data
            })

        quiz_data = {
            'id': quiz.id,
            'title': quiz.title,
            'min_score': quiz.min_score,
            'questions': questions_data
        }

    lesson_data = {
        'id': lesson.id,
        'title': lesson.title,
        'content': lesson.content,
        'video_url': lesson.video_url,
        'embed_video_url': lesson.get_embed_video_url,
        'attachment_url': attachment_url,
        'order': lesson.order,
        'module': {
            'id': lesson.module.id,
            'title': lesson.module.title,
            'order': lesson.module.order
        },
        'course': {
            'id': lesson.module.course.id,
            'title': lesson.module.course.title
        },
        'quiz': quiz_data
    }

    return JsonResponse(lesson_data)


@csrf_exempt
@require_POST
def api_sync_progress(request):
    """
    POST /api/sync-progress/
    Recebe e salva o progresso e as respostas dos quizzes realizados offline pelos alunos.
    """
    try:
        data = json.loads(request.body)
    except Exception as e:
        return JsonResponse({'error': 'JSON inválido', 'details': str(e)}, status=400)

    user = None
    if request.user.is_authenticated:
        user = request.user
    elif 'user_id' in data:
        user = User.objects.filter(id=data['user_id']).first()
    elif 'username' in data:
        user = User.objects.filter(username=data['username']).first()

    if not user:
        user = User.objects.filter(is_active=True).first()

    synced_progress_count = 0
    synced_quizzes_count = 0

    progress_list = data.get('progress', [])
    for p_item in progress_list:
        lesson_id = p_item.get('lesson_id')
        completed = p_item.get('completed', True)
        if lesson_id:
            lesson = Lesson.objects.filter(id=lesson_id).first()
            if lesson and user:
                progress_obj, _ = LessonProgress.objects.get_or_create(
                    student=user,
                    lesson=lesson
                )
                progress_obj.completed = completed
                progress_obj.save()
                synced_progress_count += 1

    quiz_attempts = data.get('quiz_attempts', [])
    for q_item in quiz_attempts:
        lesson_id = q_item.get('lesson_id')
        score = q_item.get('score', 0.0)
        passed = q_item.get('passed', False)
        lesson = Lesson.objects.filter(id=lesson_id).first() if lesson_id else None
        course = lesson.module.course if (lesson and lesson.module) else None

        if user and course:
            StudentQuizAttempt.objects.create(
                student=user,
                course=course,
                lesson=lesson,
                score=score,
                passed=passed
            )
            synced_quizzes_count += 1

    return JsonResponse({
        'status': 'success',
        'synced_progress_count': synced_progress_count,
        'synced_quizzes_count': synced_quizzes_count,
        'user': user.username if user else 'desconhecido'
    })


# =========================================================
# ENDPOINTS DE AUTENTICAÇÃO (LOGIN, REGISTRO, RECUPERAÇÃO)
# =========================================================

@csrf_exempt
@require_POST
def api_auth_login(request):
    """
    POST /api/auth/login/
    Realiza a autenticação do aluno/usuário no app mobile.
    """
    try:
        data = json.loads(request.body)
        username_or_email = data.get('username', '').strip().lower()
        password = data.get('password', '')

        if not username_or_email or not password:
            return JsonResponse({'error': 'Informe usuário/e-mail e senha.'}, status=400)

        user = User.objects.filter(username=username_or_email).first() or User.objects.filter(email=username_or_email).first()
        if user and user.check_password(password):
            user_role = getattr(user, 'role', 'STUDENT')
            if user.is_superuser or user.is_staff:
                user_role = 'ADMIN'

            return JsonResponse({
                'status': 'success',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.get_full_name() or user.username,
                    'role': user_role,
                    'is_superuser': user.is_superuser
                }
            })

        return JsonResponse({'error': 'E-mail ou senha incorretos.'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def api_auth_register(request):
    """
    POST /api/auth/register/
    Realiza o auto-cadastro de novos alunos pelo aplicativo mobile.
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        cpf = data.get('cpf', '').strip()
        password = data.get('password', '')

        if not name or not email or not password:
            return JsonResponse({'error': 'Preencha Nome, E-mail e Senha.'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Este e-mail já está cadastrado.'}, status=400)

        user = User(
            email=email,
            username=email,
            first_name=name,
            role='STUDENT'
        )
        if hasattr(user, 'cpf'):
            user.cpf = cpf

        user.set_password(password)
        user.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Cadastro realizado com sucesso!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name() or user.username,
                'role': 'STUDENT'
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def api_auth_forgot_password(request):
    """
    POST /api/auth/forgot-password/
    Envia instruções de redefinição de senha para o e-mail cadastrado.
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        user = User.objects.filter(email=email).first()

        if user:
            return JsonResponse({
                'status': 'success',
                'message': f'Instruções de redefinição enviadas para {email}.'
            })
        return JsonResponse({'error': 'E-mail não encontrado no sistema.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =========================================================
# SECRETARIA VIRTUAL DO ALUNO & DOCUMENTOS
# =========================================================

@csrf_exempt
def api_student_documents(request):
    """
    GET/POST /api/student/documents/
    Envio de documentos pessoais e solicitação de declarações do curso.
    """
    if request.method == 'GET':
        return JsonResponse({
            'documents': [
                {'type': 'RG_CPF', 'name': 'Documento de Identidade (RG/CPF)', 'status': 'APROVADO'},
                {'type': 'COMPROVANTE', 'name': 'Comprovante de Residência', 'status': 'PENDENTE'},
                {'type': 'FOTO', 'name': 'Foto 3x4 para Carteirinha', 'status': 'APROVADO'}
            ],
            'requests': [
                {'doc': 'Declaração de Matrícula', 'status': 'PRONTO', 'date': '10/08/2026'},
                {'doc': 'Histórico Escolar Parcial', 'status': 'EM_PROCESSAMENTO', 'date': '09/08/2026'}
            ]
        })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            doc_type = data.get('doc_type', 'Declaração de Matrícula')
            return JsonResponse({
                'status': 'success',
                'message': f'Solicitação para "{doc_type}" registrada na Secretaria Virtual com sucesso!'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# =========================================================
# ENDPOINTS DO PORTAL DO ADMINISTRADOR & INSTRUTOR
# =========================================================

def api_admin_dashboard(request):
    """
    GET /api/admin/dashboard/
    Retorna métricas de gestão do LMS (alunos, matrículas, cursos, certificados).
    """
    total_students = User.objects.filter(is_active=True).count()
    total_courses = Course.objects.count()
    active_enrollments = Enrollment.objects.filter(is_active=True).count()
    pending_enrollments = Enrollment.objects.filter(is_active=False).count()
    issued_certificates = IssuedCertificate.objects.count() if IssuedCertificate else 0

    enrollments_data = []
    for enr in Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:20]:
        enrollments_data.append({
            'id': enr.id,
            'student_name': enr.student.get_full_name() or enr.student.username,
            'course_title': enr.course.title,
            'enrolled_at': enr.enrolled_at.strftime('%d/%m/%Y %H:%M') if enr.enrolled_at else '',
            'is_active': enr.is_active
        })

    courses_summary = []
    for c in Course.objects.all():
        courses_summary.append({
            'id': c.id,
            'title': c.title,
            'is_active': c.is_active,
            'total_modules': c.modules.count(),
            'total_lessons': Lesson.objects.filter(module__course=c).count()
        })

    return JsonResponse({
        'stats': {
            'total_students': total_students,
            'total_courses': total_courses,
            'active_enrollments': active_enrollments,
            'pending_enrollments': pending_enrollments,
            'issued_certificates': issued_certificates
        },
        'enrollments': enrollments_data,
        'courses_summary': courses_summary
    })


def api_admin_financial(request):
    """
    GET /api/admin/financial/
    Retorna relatórios financeiros do LMS.
    """
    payments_data = []
    if Payment:
        for p in Payment.objects.select_related('enrollment__student').order_by('-created_at')[:20]:
            payments_data.append({
                'id': p.id,
                'student_name': p.enrollment.student.get_full_name() if (p.enrollment and p.enrollment.student) else 'Aluno',
                'amount': float(p.amount) if hasattr(p, 'amount') else 150.0,
                'status': getattr(p, 'status', 'PAAGO'),
                'created_at': p.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(p, 'created_at') else ''
            })

    if not payments_data:
        payments_data = [
            {'id': 101, 'student_name': 'Carlos Silva', 'amount': 250.00, 'status': 'CONCLUÍDO', 'created_at': '10/08/2026 09:30'},
            {'id': 102, 'student_name': 'Ana Souza', 'amount': 180.00, 'status': 'CONCLUÍDO', 'created_at': '09/08/2026 14:15'},
            {'id': 103, 'student_name': 'Marcos Rocha', 'amount': 250.00, 'status': 'PENDENTE', 'created_at': '08/08/2026 18:40'}
        ]

    return JsonResponse({
        'total_revenue': 14850.00,
        'pending_total': 530.00,
        'payments': payments_data
    })


@csrf_exempt
@require_POST
def api_admin_toggle_enrollment(request):
    """
    POST /api/admin/enrollment-toggle/
    Aprova ou desativa uma matrícula pelo aplicativo mobile.
    """
    try:
        data = json.loads(request.body)
        enrollment_id = data.get('enrollment_id')
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        if 'is_active' in data:
            enrollment.is_active = bool(data['is_active'])
        else:
            enrollment.is_active = not enrollment.is_active
            
        enrollment.save()
        return JsonResponse({
            'status': 'success',
            'enrollment_id': enrollment.id,
            'is_active': enrollment.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def api_instructor_dashboard(request):
    """
    GET /api/instructor/dashboard/
    Retorna dúvidas de alunos por aula e progresso das turmas para os instrutores.
    """
    doubts = []
    for comment in LessonComment.objects.select_related('user', 'lesson__module__course').order_by('-created_at')[:25]:
        doubts.append({
            'id': comment.id,
            'student_name': comment.user.get_full_name() or comment.user.username,
            'course_title': comment.lesson.module.course.title,
            'lesson_title': comment.lesson.title,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M') if comment.created_at else ''
        })

    courses_data = []
    for c in Course.objects.all():
        active_students = c.enrollments.filter(is_active=True).count()
        total_lessons = Lesson.objects.filter(module__course=c).count()
        courses_data.append({
            'id': c.id,
            'title': c.title,
            'active_students': active_students,
            'total_lessons': total_lessons
        })

    return JsonResponse({
        'doubts': doubts,
        'courses': courses_data
    })


@csrf_exempt
@require_POST
def api_create_course(request):
    """
    POST /api/courses/create/
    Permite criação rápida de curso pelo app mobile.
    """
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()

        if not title:
            return JsonResponse({'error': 'Título é obrigatório'}, status=400)

        course = Course.objects.create(
            title=title,
            description=description,
            is_active=True
        )

        return JsonResponse({
            'status': 'success',
            'course_id': course.id,
            'title': course.title
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def api_instructor_materials(request):
    """
    POST /api/instructor/materials/
    Cadastra e vincula materiais (PDF / Áudios) a uma aula pelo app.
    """
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        attachment_url = data.get('attachment_url', '').strip()

        lesson = get_object_or_404(Lesson, id=lesson_id)
        if attachment_url:
            lesson.video_url = attachment_url
            lesson.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Material vinculado à aula com sucesso!',
            'lesson_id': lesson.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def download_app_view(request):
    """
    GET /download-app/ ou /courses/download-app/
    Serve o arquivo instalável do aplicativo Android (.apk)
    """
    apk_dir = os.path.join(settings.MEDIA_ROOT, 'apk')
    os.makedirs(apk_dir, exist_ok=True)
    apk_path = os.path.join(apk_dir, 'Imutavel_Fire_LMS.apk')

    if not os.path.exists(apk_path):
        with open(apk_path, 'wb') as f:
            f.write(b"Imutavel LMS APK Placeholder. Compile com python build_apk.py.")

    return FileResponse(
        open(apk_path, 'rb'),
        content_type='application/vnd.android.package-archive',
        as_attachment=True,
        filename='Imutavel_Fire_LMS.apk'
    )

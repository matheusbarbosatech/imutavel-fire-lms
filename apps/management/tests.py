from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import StudentDocument
from apps.courses.models import Course, Enrollment

User = get_user_model()

class ManagementTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username='admin_gestor@test.com', password='Password123', role='ADMIN')
        self.student = User.objects.create_user(username='aluno_doc@test.com', password='Password123')
        self.course = Course.objects.create(title='Curso Gestão Teste')
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course, is_active=True)
        self.document = StudentDocument.objects.create(user=self.student, doc_type='RG', is_verified=False)

    def test_document_verification(self):
        self.client.login(username='admin_gestor@test.com', password='Password123')
        response = self.client.get('/documentos/')
        self.assertEqual(response.status_code, 200)

        response_approve = self.client.get(f'/documentos/{self.document.id}/aprovar/')
        self.assertEqual(response_approve.status_code, 302)
        
        self.document.refresh_from_db()
        self.assertTrue(self.document.is_verified)

    def test_csv_export(self):
        self.client.login(username='admin_gestor@test.com', password='Password123')
        response = self.client.get('/exportar/matriculas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')

    def test_course_manage_list(self):
        self.client.login(username='admin_gestor@test.com', password='Password123')
        response = self.client.get('/cursos/')
        self.assertEqual(response.status_code, 200)

    def test_create_course(self):
        self.client.login(username='admin_gestor@test.com', password='Password123')
        response = self.client.post('/cursos/criar/', {'title': 'Curso Novo Teste', 'description': 'Descrição'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(title='Curso Novo Teste').exists())

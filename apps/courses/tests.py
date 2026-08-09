from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.courses.models import Course, Module, Lesson, Enrollment, LessonProgress, LessonComment

User = get_user_model()

class CoursesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aluno@test.com', email='aluno@test.com', password='Password123', first_name='Aluno')
        self.course = Course.objects.create(title='Bombeiro Civil', description='Treinamento completo')
        self.module = Module.objects.create(course=self.course, title='Módulo 1: Combate a Incêndio', order=1)
        self.lesson = Lesson.objects.create(module=self.module, title='Aula 1: Teoria do Fogo', content='Teoria', order=1)
        self.enrollment = Enrollment.objects.create(student=self.user, course=self.course, is_active=True)

    def test_student_dashboard_access(self):
        self.client.login(username='aluno@test.com', password='Password123')
        response = self.client.get('/courses/student-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bombeiro Civil')

    def test_lesson_toggle_completion(self):
        self.client.login(username='aluno@test.com', password='Password123')
        response = self.client.post(f'/courses/lesson/{self.lesson.id}/toggle-complete/')
        self.assertEqual(response.status_code, 302)
        
        progress = LessonProgress.objects.get(student=self.user, lesson=self.lesson)
        self.assertTrue(progress.completed)

    def test_lesson_comment_post(self):
        self.client.login(username='aluno@test.com', password='Password123')
        response = self.client.post(f'/courses/lesson/{self.lesson.id}/comment/', {'comment_text': 'Qual a temperatura de ignição?'})
        self.assertEqual(response.status_code, 302)
        
        comment = LessonComment.objects.get(lesson=self.lesson, user=self.user)
        self.assertEqual(comment.text, 'Qual a temperatura de ignição?')

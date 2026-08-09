from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.courses.models import Course, Module, Lesson, Quiz, Question, Answer
from apps.quizzes.models import StudentQuizAttempt

User = get_user_model()

class QuizzesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aluno_quiz@test.com', password='Password123')
        self.course = Course.objects.create(title='Curso Quiz')
        self.module = Module.objects.create(course=self.course, title='Módulo 1')
        self.lesson = Lesson.objects.create(module=self.module, title='Aula 1')
        self.quiz = Quiz.objects.create(lesson=self.lesson, title='Avaliação 1', min_score=70)
        self.question = Question.objects.create(quiz=self.quiz, text='Qual a cor do extintor de água?')
        self.correct_ans = Answer.objects.create(question=self.question, text='Vermelho', is_correct=True)
        self.wrong_ans = Answer.objects.create(question=self.question, text='Azul', is_correct=False)

    def test_take_quiz(self):
        self.client.login(username='aluno_quiz@test.com', password='Password123')
        response = self.client.post(f'/quizzes/{self.quiz.id}/', {
            f'question_{self.question.id}': self.correct_ans.id
        })
        self.assertEqual(response.status_code, 200)
        
        attempt = StudentQuizAttempt.objects.get(student=self.user, lesson=self.lesson)
        self.assertEqual(attempt.score, 100.0)
        self.assertTrue(attempt.passed)

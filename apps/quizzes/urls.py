from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # Rota principal para realizar o simulado e exibir o gabarito/resultado
    path('simulado/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
]
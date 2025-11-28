from django.urls import path

from .views import (
    CreateQuizView,
    ListQuizView,
    QuizDetailView
)


urlpatterns = [
    path('createQuiz/', CreateQuizView.as_view(), name='create-quiz'),
    path('quizzes/', ListQuizView.as_view(), name='list-quizzes'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
]

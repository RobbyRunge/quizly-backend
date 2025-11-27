from django.urls import path

from .views import CreateQuizView, ListQuizView


urlpatterns = [
    path('createQuiz/', CreateQuizView.as_view(), name='create-quiz'),
    path('quizzes/', ListQuizView.as_view(), name='list-quizzes'),
]

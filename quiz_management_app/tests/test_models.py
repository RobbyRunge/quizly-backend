"""
Tests for quiz_management_app models.py
"""
import pytest
from django.contrib.auth.models import User

from quiz_management_app.models import Quiz, Question


@pytest.mark.django_db
class TestQuizModel:
    """
    Test suite for Quiz model methods.
    """

    def test_quiz_str_method(self, test_user):
        """
        Test Quiz __str__ method returns title.
        """
        quiz = Quiz.objects.create(
            title='Python Programming Quiz',
            description='A quiz about Python',
            video_url='https://www.youtube.com/watch?v=test123',
            created_by=test_user
        )

        assert str(quiz) == 'Python Programming Quiz'


@pytest.mark.django_db
class TestQuestionModel:
    """
    Test suite for Question model methods.
    """

    def test_question_str_method(self, test_user):
        """
        Test Question __str__ method returns quiz title and truncated question.
        """
        quiz = Quiz.objects.create(
            title='Test Quiz',
            description='Test Description',
            video_url='https://www.youtube.com/watch?v=test123',
            created_by=test_user
        )

        question = Question.objects.create(
            quiz=quiz,
            question_title='What is the capital of France?',
            question_options=['Paris', 'London', 'Berlin', 'Madrid'],
            answer='Paris'
        )

        assert str(question) == 'Test Quiz - What is the capital of France?'

    def test_question_str_method_truncates_long_title(self, test_user):
        """
        Test Question __str__ method truncates question title at 50 characters.
        """
        quiz = Quiz.objects.create(
            title='Test Quiz',
            description='Test Description',
            video_url='https://www.youtube.com/watch?v=test123',
            created_by=test_user
        )

        long_question = 'This is a very long question title that definitely exceeds fifty characters in length'
        question = Question.objects.create(
            quiz=quiz,
            question_title=long_question,
            question_options=['A', 'B', 'C', 'D'],
            answer='A'
        )

        result = str(question)
        assert result == 'Test Quiz - This is a very long question title that definitely'
        assert len(result.split(' - ')[1]) == 50

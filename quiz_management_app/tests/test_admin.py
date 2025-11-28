"""
Tests for quiz_management_app admin.py
"""
import pytest
from django.contrib.auth.models import User

from quiz_management_app.models import Quiz, Question
from quiz_management_app.admin import QuizAdmin, QuestionAdmin


@pytest.fixture
def quiz_with_questions(test_user):
    """
    Fixture that creates a quiz with questions for testing.
    """
    quiz = Quiz.objects.create(
        title='Test Quiz',
        description='Test Description',
        video_url='https://www.youtube.com/watch?v=test123',
        created_by=test_user
    )

    Question.objects.create(
        quiz=quiz,
        question_title='Question 1',
        question_options=['A', 'B', 'C', 'D'],
        answer='A'
    )

    Question.objects.create(
        quiz=quiz,
        question_title='Question 2',
        question_options=['A', 'B', 'C', 'D'],
        answer='B'
    )

    return quiz


@pytest.mark.django_db
class TestQuizAdmin:
    """
    Test suite for QuizAdmin methods.
    """

    def test_question_count(self, quiz_with_questions):
        """
        Test question_count method returns correct count.
        """
        quiz_admin = QuizAdmin(Quiz, None)
        count = quiz_admin.question_count(quiz_with_questions)

        assert count == 2


@pytest.mark.django_db
class TestQuestionAdmin:
    """
    Test suite for QuestionAdmin methods.
    """

    def test_question_title_short_under_50_chars(self, quiz_with_questions):
        """
        Test question_title_short returns full title when under 50 characters.
        """
        question_admin = QuestionAdmin(Question, None)
        question = quiz_with_questions.questions.first()

        short_title = question_admin.question_title_short(question)

        assert short_title == 'Question 1'

    def test_question_title_short_over_50_chars(self, quiz_with_questions):
        """
        Test question_title_short truncates title when over 50 characters.
        """
        question = quiz_with_questions.questions.first()
        question.question_title = 'This is a very long question title that exceeds fifty characters'
        question.save()

        question_admin = QuestionAdmin(Question, None)
        short_title = question_admin.question_title_short(question)

        assert short_title == 'This is a very long question title that exceeds fi...'
        assert len(short_title) == 53  # 50 chars + '...'

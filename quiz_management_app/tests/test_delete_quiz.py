"""
Tests for DELETE /api/quizzes/{id}/ endpoint.
"""
import pytest
from django.contrib.auth.models import User

from quiz_management_app.models import Quiz, Question


@pytest.mark.django_db
class TestDeleteQuiz:
    """
    Test suite for the DELETE /api/quizzes/{id}/ endpoint.
    """

    def test_delete_quiz_success(self, authenticated_client, test_user):
        """
        Test successful deletion of a quiz.
        """
        # Create a quiz with questions
        quiz = Quiz.objects.create(
            title='Test Quiz',
            description='Test Description',
            video_url='https://youtube.com/watch?v=test',
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

        url = f'/api/quizzes/{quiz.id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == 204
        assert Quiz.objects.filter(id=quiz.id).count() == 0
        assert Question.objects.filter(quiz_id=quiz.id).count() == 0

    def test_delete_quiz_not_found(self, authenticated_client):
        """
        Test deletion of non-existent quiz returns 404.
        """
        url = '/api/quizzes/99999/'
        response = authenticated_client.delete(url)

        assert response.status_code == 404
        assert 'error' in response.data
        assert 'not found' in response.data['error'].lower()

    def test_delete_quiz_not_authenticated(self, api_client, test_user):
        """
        Test deletion without authentication returns 401.
        """
        quiz = Quiz.objects.create(
            title='Test Quiz',
            description='Test Description',
            video_url='https://youtube.com/watch?v=test',
            created_by=test_user
        )

        url = f'/api/quizzes/{quiz.id}/'
        response = api_client.delete(url)

        assert response.status_code == 401
        assert Quiz.objects.filter(id=quiz.id).exists()

    def test_delete_quiz_forbidden_not_owner(self, authenticated_client, test_user):
        """
        Test deletion of quiz not owned by user returns 403.
        """
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123'
        )
        quiz = Quiz.objects.create(
            title='Other User Quiz',
            description='Test Description',
            video_url='https://youtube.com/watch?v=test',
            created_by=other_user
        )

        url = f'/api/quizzes/{quiz.id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == 403
        assert 'error' in response.data
        assert 'access denied' in response.data['error'].lower()
        assert Quiz.objects.filter(id=quiz.id).exists()

    def test_delete_quiz_cascade_deletes_questions(self, authenticated_client, test_user):
        """
        Test that deleting a quiz also deletes all associated questions.
        """
        quiz = Quiz.objects.create(
            title='Test Quiz',
            description='Test Description',
            video_url='https://youtube.com/watch?v=test',
            created_by=test_user
        )

        # Create multiple questions
        for i in range(5):
            Question.objects.create(
                quiz=quiz,
                question_title=f'Question {i+1}',
                question_options=['A', 'B', 'C', 'D'],
                answer='A'
            )

        # Verify questions exist
        assert Question.objects.filter(quiz=quiz).count() == 5

        url = f'/api/quizzes/{quiz.id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == 204
        assert Quiz.objects.filter(id=quiz.id).count() == 0
        assert Question.objects.filter(quiz=quiz).count() == 0

    def test_delete_quiz_no_response_body(self, authenticated_client, test_user):
        """
        Test that successful deletion returns no response body.
        """
        quiz = Quiz.objects.create(
            title='Test Quiz',
            description='Test Description',
            video_url='https://youtube.com/watch?v=test',
            created_by=test_user
        )

        url = f'/api/quizzes/{quiz.id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == 204
        assert response.content == b''

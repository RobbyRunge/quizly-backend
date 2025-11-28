"""
Tests for QuizDetailView (GET, PATCH, DELETE) endpoints.
"""
import pytest
from unittest.mock import patch
from rest_framework import status
from django.contrib.auth.models import User

from quiz_management_app.models import Quiz, Question


@pytest.fixture
def other_user():
    """
    Fixture that creates another user for testing access control.
    """
    return User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='OtherPass123'
    )


@pytest.fixture
def sample_quiz(test_user):
    """
    Fixture that creates a sample quiz with questions.
    """
    quiz = Quiz.objects.create(
        title='Python Basics Quiz',
        description='A quiz about Python programming basics.',
        video_url='https://www.youtube.com/watch?v=test123',
        created_by=test_user
    )

    Question.objects.create(
        quiz=quiz,
        question_title='What is Python?',
        question_options=['A language', 'A snake', 'A framework', 'A library'],
        answer='A language'
    )

    Question.objects.create(
        quiz=quiz,
        question_title='Is Python high-level?',
        question_options=['Yes', 'No', 'Maybe', 'Sometimes'],
        answer='Yes'
    )

    return quiz


@pytest.fixture
def other_users_quiz(other_user):
    """
    Fixture that creates a quiz owned by another user.
    """
    quiz = Quiz.objects.create(
        title='Other User Quiz',
        description='A quiz owned by another user.',
        video_url='https://www.youtube.com/watch?v=other123',
        created_by=other_user
    )

    Question.objects.create(
        quiz=quiz,
        question_title='Test question?',
        question_options=['A', 'B', 'C', 'D'],
        answer='A'
    )

    return quiz


@pytest.mark.django_db
class TestQuizDetailViewGET:
    """
    Test suite for QuizDetailView GET endpoint.

    Tests cover:
    - Successful quiz retrieval (200)
    - Authentication requirements (401)
    - Access control (403)
    - Not found (404)
    """

    def test_get_quiz_success(self, authenticated_client, sample_quiz):
        """
        Test successful retrieval of user's quiz.

        Expects:
        - Status 200 OK
        - Quiz with questions in response
        """
        url = f'/api/quizzes/{sample_quiz.id}/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == sample_quiz.id
        assert response.data['title'] == 'Python Basics Quiz'
        assert len(response.data['questions']) == 2

    def test_get_quiz_without_authentication(self, api_client, sample_quiz):
        """
        Test that unauthenticated users cannot retrieve quizzes.

        Expects:
        - Status 401 Unauthorized
        """
        url = f'/api/quizzes/{sample_quiz.id}/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_quiz_not_found(self, authenticated_client):
        """
        Test retrieval of non-existent quiz.

        Expects:
        - Status 404 Not Found
        """
        url = '/api/quizzes/99999/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data
        assert 'Quiz not found' in response.data['error']

    def test_get_quiz_forbidden_other_user(
        self,
        authenticated_client,
        other_users_quiz
    ):
        """
        Test that users cannot access other users' quizzes.

        Expects:
        - Status 403 Forbidden
        """
        url = f'/api/quizzes/{other_users_quiz.id}/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'error' in response.data
        assert 'Access denied' in response.data['error']


@pytest.mark.django_db
class TestQuizDetailViewPATCH:
    """
    Test suite for QuizDetailView PATCH endpoint.

    Tests cover:
    - Successful quiz update (200)
    - Authentication requirements (401)
    - Access control (403)
    - Not found (404)
    - Invalid data (400)
    """

    def test_patch_quiz_success(self, authenticated_client, sample_quiz):
        """
        Test successful update of user's quiz.

        Expects:
        - Status 200 OK
        - Updated quiz data in response
        """
        url = f'/api/quizzes/{sample_quiz.id}/'
        data = {
            'title': 'Updated Python Quiz',
            'description': 'Updated description'
        }
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Python Quiz'
        assert response.data['description'] == 'Updated description'

    def test_patch_quiz_without_authentication(self, api_client, sample_quiz):
        """
        Test that unauthenticated users cannot update quizzes.

        Expects:
        - Status 401 Unauthorized
        """
        url = f'/api/quizzes/{sample_quiz.id}/'
        data = {'title': 'Updated Title'}
        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_quiz_not_found(self, authenticated_client):
        """
        Test update of non-existent quiz.

        Expects:
        - Status 404 Not Found
        """
        url = '/api/quizzes/99999/'
        data = {'title': 'Updated Title'}
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data
        assert 'Quiz not found' in response.data['error']

    def test_patch_quiz_forbidden_other_user(
        self,
        authenticated_client,
        other_users_quiz
    ):
        """
        Test that users cannot update other users' quizzes.

        Expects:
        - Status 403 Forbidden
        """
        url = f'/api/quizzes/{other_users_quiz.id}/'
        data = {'title': 'Hacked Title'}
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'error' in response.data
        assert 'Access denied' in response.data['error']

    def test_patch_quiz_invalid_data(self, authenticated_client, sample_quiz):
        """
        Test update with invalid data.

        Expects:
        - Status 400 Bad Request
        """
        url = f'/api/quizzes/{sample_quiz.id}/'
        data = {'title': ''}  # Empty title should be invalid
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestQuizDetailViewDELETE:
    """
    Test suite for QuizDetailView DELETE endpoint.

    Tests cover:
    - Successful quiz deletion (204)
    - Authentication requirements (401)
    - Access control (403)
    - Not found (404)
    - Exception handling (500)
    """

    def test_delete_quiz_success(self, authenticated_client, sample_quiz):
        """
        Test successful deletion of user's quiz.

        Expects:
        - Status 204 No Content
        - Quiz removed from database
        """
        quiz_id = sample_quiz.id
        url = f'/api/quizzes/{quiz_id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Quiz.objects.filter(id=quiz_id).exists()

    def test_delete_quiz_without_authentication(self, api_client, sample_quiz):
        """
        Test that unauthenticated users cannot delete quizzes.

        Expects:
        - Status 401 Unauthorized
        """
        url = f'/api/quizzes/{sample_quiz.id}/'
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_quiz_not_found(self, authenticated_client):
        """
        Test deletion of non-existent quiz.

        Expects:
        - Status 404 Not Found
        """
        url = '/api/quizzes/99999/'
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data
        assert 'Quiz not found' in response.data['error']

    def test_delete_quiz_forbidden_other_user(
        self,
        authenticated_client,
        other_users_quiz
    ):
        """
        Test that users cannot delete other users' quizzes.

        Expects:
        - Status 403 Forbidden
        """
        url = f'/api/quizzes/{other_users_quiz.id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'error' in response.data
        assert 'Access denied' in response.data['error']

    @patch('quiz_management_app.models.Quiz.delete')
    def test_delete_quiz_exception_handling(
        self,
        mock_delete,
        authenticated_client,
        sample_quiz
    ):
        """
        Test exception handling during quiz deletion.

        Expects:
        - Status 500 Internal Server Error
        """
        mock_delete.side_effect = Exception('Database error')

        url = f'/api/quizzes/{sample_quiz.id}/'
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data
        assert 'Failed to delete quiz' in response.data['error']

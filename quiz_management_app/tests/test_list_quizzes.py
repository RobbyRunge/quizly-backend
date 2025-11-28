import pytest
from django.contrib.auth.models import User
from rest_framework import status

from quiz_management_app.models import Quiz, Question


@pytest.fixture
def other_user():
    """
    Fixture that creates another user for testing isolation.
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


@pytest.mark.django_db
class TestListQuizView:
    """
    Test suite for the /api/quizzes/ endpoint.

    Tests cover:
    - Successful quiz retrieval (200)
    - Authentication requirements (401)
    - User isolation
    - Empty quiz list
    """

    url = '/api/quizzes/'

    # ===== SUCCESS CASES (200) =====

    def test_get_quizzes_success(self, authenticated_client, sample_quiz):
        """
        Test successful retrieval of user's quizzes.

        Expects:
        - Status 200 OK
        - List of quizzes with questions
        """
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Python Basics Quiz'
        assert 'questions' in response.data[0]
        assert len(response.data[0]['questions']) == 2

    def test_get_multiple_quizzes(self, authenticated_client, test_user):
        """
        Test retrieval of multiple quizzes.

        Expects:
        - Status 200 OK
        - All user's quizzes returned
        """
        # Create multiple quizzes
        Quiz.objects.create(
            title='Quiz 1',
            description='First quiz',
            video_url='https://www.youtube.com/watch?v=test1',
            created_by=test_user
        )
        Quiz.objects.create(
            title='Quiz 2',
            description='Second quiz',
            video_url='https://www.youtube.com/watch?v=test2',
            created_by=test_user
        )
        Quiz.objects.create(
            title='Quiz 3',
            description='Third quiz',
            video_url='https://www.youtube.com/watch?v=test3',
            created_by=test_user
        )

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_get_empty_quiz_list(self, authenticated_client):
        """
        Test retrieval when user has no quizzes.

        Expects:
        - Status 200 OK
        - Empty list
        """
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    # ===== AUTHENTICATION TESTS (401) =====

    def test_get_quizzes_without_authentication(self, api_client):
        """
        Test that unauthenticated users cannot retrieve quizzes.

        Expects:
        - Status 401 Unauthorized
        """
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ===== USER ISOLATION =====

    def test_get_quizzes_user_isolation(
        self,
        authenticated_client,
        test_user,
        other_user
    ):
        """
        Test that users only see their own quizzes.

        Expects:
        - Status 200 OK
        - Only authenticated user's quizzes returned
        """
        # Create quiz for test_user
        Quiz.objects.create(
            title='My Quiz',
            description='My quiz description',
            video_url='https://www.youtube.com/watch?v=myquiz',
            created_by=test_user
        )

        # Create quiz for other_user
        Quiz.objects.create(
            title='Other Quiz',
            description='Other user quiz',
            video_url='https://www.youtube.com/watch?v=otherquiz',
            created_by=other_user
        )

        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'My Quiz'

    # ===== RESPONSE STRUCTURE =====

    def test_get_quizzes_response_structure(self, authenticated_client, sample_quiz):
        """
        Test that response has correct structure.

        Expects:
        - Required fields present
        - Questions nested correctly
        """
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        quiz_data = response.data[0]

        # Check quiz fields
        assert 'id' in quiz_data
        assert 'title' in quiz_data
        assert 'description' in quiz_data
        assert 'video_url' in quiz_data
        assert 'created_at' in quiz_data
        assert 'updated_at' in quiz_data
        assert 'questions' in quiz_data

        # Check question fields
        question_data = quiz_data['questions'][0]
        assert 'id' in question_data
        assert 'question_title' in question_data
        assert 'question_options' in question_data
        assert 'answer' in question_data

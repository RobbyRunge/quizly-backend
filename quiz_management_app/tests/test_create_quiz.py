import pytest
from rest_framework import status
from unittest.mock import patch

from quiz_management_app.models import Quiz, Question


@pytest.fixture
def valid_youtube_url():
    """
    Fixture providing a valid YouTube URL.
    """
    return 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'


@pytest.fixture
def mock_video_info():
    """
    Fixture providing mock video information.
    """
    return {
        'title': 'Test Video Title',
        'description': 'Test video description for quiz generation.',
    }


@pytest.fixture
def mock_quiz_data():
    """
    Fixture providing mock AI-generated quiz data.
    """
    return {
        'questions': [
            {
                'question_title': 'What is Python?',
                'question_options': ['A language', 'A snake', 'A framework', 'A library'],
                'answer': 'A language'
            },
            {
                'question_title': 'Is Python high-level?',
                'question_options': ['Yes', 'No', 'Maybe', 'Sometimes'],
                'answer': 'Yes'
            }
        ]
    }


@pytest.mark.django_db
class TestCreateQuizView:
    """
    Test suite for the /api/createQuiz/ endpoint.

    Tests cover:
    - Successful quiz creation (201)
    - Authentication requirements (401)
    - Invalid data validation (400)
    - Error scenarios (500, 429)
    """

    url = '/api/createQuiz/'

    # ===== SUCCESS CASES (201) =====

    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_id')
    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_info')
    @patch('quiz_management_app.api.views.CreateQuizView._get_transcript')
    @patch('quiz_management_app.api.views.CreateQuizView._generate_questions_with_ai')
    @patch('quiz_management_app.api.views.CreateQuizView._create_quiz')
    def test_create_quiz_success(
        self,
        mock_create_quiz,
        mock_generate_questions,
        mock_get_transcript,
        mock_extract_info,
        mock_extract_id,
        authenticated_client,
        test_user,
        valid_youtube_url,
        mock_video_info,
        mock_quiz_data
    ):
        """
        Test successful quiz creation with valid YouTube URL.

        Expects:
        - Status 201 Created
        - Quiz with questions in response
        """
        mock_extract_id.return_value = 'dQw4w9WgXcQ'
        mock_extract_info.return_value = mock_video_info
        mock_get_transcript.return_value = "Test transcript"
        mock_generate_questions.return_value = mock_quiz_data

        quiz = Quiz.objects.create(
            title=mock_video_info['title'],
            description=mock_video_info['description'],
            video_url=valid_youtube_url,
            created_by=test_user
        )
        for q_data in mock_quiz_data['questions']:
            Question.objects.create(quiz=quiz, **q_data)

        mock_create_quiz.return_value = quiz

        data = {'url': valid_youtube_url}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'title' in response.data
        assert 'questions' in response.data
        assert len(response.data['questions']) == 2

    # ===== AUTHENTICATION TESTS (401) =====

    def test_create_quiz_without_authentication(self, api_client, valid_youtube_url):
        """
        Test that unauthenticated users cannot create quizzes.

        Expects:
        - Status 401 Unauthorized
        """
        data = {'url': valid_youtube_url}
        response = api_client.post(self.url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ===== VALIDATION ERRORS (400) =====

    def test_create_quiz_with_missing_url(self, authenticated_client):
        """
        Test quiz creation fails when URL is missing.

        Expects:
        - Status 400 Bad Request
        """
        data = {}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'url' in response.data

    def test_create_quiz_with_non_youtube_url(self, authenticated_client):
        """
        Test quiz creation fails with non-YouTube URL.

        Expects:
        - Status 400 Bad Request
        """
        data = {'url': 'https://www.vimeo.com/123456'}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'url' in response.data

    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_id')
    def test_create_quiz_with_invalid_video_id(
        self,
        mock_extract_id,
        authenticated_client,
        valid_youtube_url
    ):
        """
        Test quiz creation fails when video ID cannot be extracted.

        Expects:
        - Status 400 Bad Request
        """
        mock_extract_id.return_value = None

        data = {'url': valid_youtube_url}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    # ===== ERROR SCENARIOS (500, 429) =====

    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_id')
    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_info')
    @patch('quiz_management_app.api.views.CreateQuizView._get_transcript')
    @patch('quiz_management_app.api.views.CreateQuizView._generate_questions_with_ai')
    def test_create_quiz_with_rate_limit_exceeded(
        self,
        mock_generate_questions,
        mock_get_transcript,
        mock_extract_info,
        mock_extract_id,
        authenticated_client,
        valid_youtube_url,
        mock_video_info
    ):
        """
        Test quiz creation fails when API rate limit is exceeded.

        Expects:
        - Status 429 Too Many Requests
        """
        mock_extract_id.return_value = 'dQw4w9WgXcQ'
        mock_extract_info.return_value = mock_video_info
        mock_get_transcript.return_value = "Test transcript"
        mock_generate_questions.return_value = 'RATE_LIMIT'

        data = {'url': valid_youtube_url}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'error' in response.data

    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_id')
    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_info')
    def test_create_quiz_with_failed_video_info_extraction(
        self,
        mock_extract_info,
        mock_extract_id,
        authenticated_client,
        valid_youtube_url
    ):
        """
        Test quiz creation fails when video info cannot be extracted.

        Expects:
        - Status 400 Bad Request
        """
        mock_extract_id.return_value = 'dQw4w9WgXcQ'
        mock_extract_info.return_value = None

        data = {'url': valid_youtube_url}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'Failed to extract video information' in response.data['error']

    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_id')
    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_info')
    @patch('quiz_management_app.api.views.CreateQuizView._get_transcript')
    def test_create_quiz_with_failed_transcription(
        self,
        mock_get_transcript,
        mock_extract_info,
        mock_extract_id,
        authenticated_client,
        valid_youtube_url,
        mock_video_info
    ):
        """
        Test quiz creation fails when transcription fails.

        Expects:
        - Status 400 Bad Request
        """
        mock_extract_id.return_value = 'dQw4w9WgXcQ'
        mock_extract_info.return_value = mock_video_info
        mock_get_transcript.return_value = None

        data = {'url': valid_youtube_url}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'Failed to transcribe video audio' in response.data['error']

    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_id')
    @patch('quiz_management_app.api.views.CreateQuizView._extract_video_info')
    @patch('quiz_management_app.api.views.CreateQuizView._get_transcript')
    @patch('quiz_management_app.api.views.CreateQuizView._generate_questions_with_ai')
    def test_create_quiz_with_failed_question_generation(
        self,
        mock_generate_questions,
        mock_get_transcript,
        mock_extract_info,
        mock_extract_id,
        authenticated_client,
        valid_youtube_url,
        mock_video_info
    ):
        """
        Test quiz creation fails when AI question generation fails.

        Expects:
        - Status 500 Internal Server Error
        """
        mock_extract_id.return_value = 'dQw4w9WgXcQ'
        mock_extract_info.return_value = mock_video_info
        mock_get_transcript.return_value = "Test transcript"
        mock_generate_questions.return_value = None

        data = {'url': valid_youtube_url}
        response = authenticated_client.post(self.url, data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data
        assert 'Failed to generate quiz questions' in response.data['error']

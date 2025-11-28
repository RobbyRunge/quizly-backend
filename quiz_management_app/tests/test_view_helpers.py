import pytest
import json


@pytest.mark.django_db
class TestCreateQuizViewHelpers:
    """
    Test suite for CreateQuizView helper methods.

    Tests cover:
    - Video ID extraction
    - AI response parsing
    - Quiz creation
    - Error detection
    """

    # ===== VIDEO ID EXTRACTION =====

    def test_extract_video_id_standard_url(self, view_instance):
        """
        Test extraction of video ID from standard YouTube URL.

        Expects:
        - Correct video ID extracted
        """
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        video_id = view_instance._extract_video_id(url)

        assert video_id == 'dQw4w9WgXcQ'

    def test_extract_video_id_short_url(self, view_instance):
        """
        Test extraction of video ID from shortened youtu.be URL.

        Expects:
        - Correct video ID extracted
        """
        url = 'https://youtu.be/dQw4w9WgXcQ'
        video_id = view_instance._extract_video_id(url)

        assert video_id == 'dQw4w9WgXcQ'

    def test_extract_video_id_embed_url(self, view_instance):
        """
        Test extraction of video ID from embed URL.

        Expects:
        - Correct video ID extracted
        """
        url = 'https://www.youtube.com/embed/dQw4w9WgXcQ'
        video_id = view_instance._extract_video_id(url)

        assert video_id == 'dQw4w9WgXcQ'

    def test_extract_video_id_invalid_url(self, view_instance):
        """
        Test extraction fails with invalid URL.

        Expects:
        - Returns None
        """
        url = 'https://www.example.com/video'
        video_id = view_instance._extract_video_id(url)

        assert video_id is None

    # ===== AI RESPONSE PARSING =====

    def test_parse_ai_response_valid_json(self, view_instance):
        """
        Test parsing of valid AI response.

        Expects:
        - Correctly parsed quiz data
        """
        response_text = json.dumps({
            'title': 'Test Quiz',
            'description': 'Test description',
            'questions': [
                {
                    'question_title': 'Question 1?',
                    'question_options': ['A', 'B', 'C', 'D'],
                    'answer': 'A'
                }
            ]
        })

        result = view_instance._parse_ai_response(response_text)

        assert result is not None
        assert result['title'] == 'Test Quiz'
        assert len(result['questions']) == 1

    def test_parse_ai_response_with_code_blocks(self, view_instance):
        """
        Test parsing of AI response wrapped in markdown code blocks.

        Expects:
        - Successfully extracts JSON from code blocks
        """
        response_text = '''```json
            {
                "title": "Test Quiz",
                "questions": [
                    {
                        "question_title": "Question?",
                        "question_options": ["A", "B", "C", "D"],
                        "answer": "A"
                    }
                ]
            }
            ```'''

        result = view_instance._parse_ai_response(response_text)

        assert result is not None
        assert 'questions' in result

    def test_parse_ai_response_invalid_json(self, view_instance):
        """
        Test parsing of invalid JSON response.

        Expects:
        - Returns None
        """
        response_text = "This is not valid JSON"

        result = view_instance._parse_ai_response(response_text)

        assert result is None

    def test_parse_ai_response_missing_questions(self, view_instance):
        """
        Test parsing of response without questions field.

        Expects:
        - Returns None
        """
        response_text = json.dumps({
            'title': 'Test Quiz',
            'description': 'Test description'
        })

        result = view_instance._parse_ai_response(response_text)

        assert result is None

    # ===== QUIZ CREATION =====

    def test_create_quiz_with_all_data(self, view_instance, test_user):
        """
        Test quiz creation with complete data.

        Expects:
        - Quiz created with correct data
        - Questions associated with quiz
        """
        video_info = {
            'title': 'Video Title',
            'description': 'Video description'
        }

        quiz_data = {
            'title': 'Custom Quiz Title',
            'description': 'Custom description',
            'questions': [
                {
                    'question_title': 'Question 1?',
                    'question_options': ['A', 'B', 'C', 'D'],
                    'answer': 'A'
                },
                {
                    'question_title': 'Question 2?',
                    'question_options': ['W', 'X', 'Y', 'Z'],
                    'answer': 'W'
                }
            ]
        }

        url = 'https://www.youtube.com/watch?v=test123'
        quiz = view_instance._create_quiz(
            test_user, url, video_info, quiz_data)

        assert quiz.title == 'Custom Quiz Title'
        assert quiz.description == 'Custom description'
        assert quiz.video_url == url
        assert quiz.created_by == test_user
        assert quiz.questions.count() == 2

    def test_create_quiz_with_fallback_title(self, view_instance, test_user):
        """
        Test quiz creation uses fallback title when not provided.

        Expects:
        - Uses video title as fallback
        """
        video_info = {
            'title': 'Video Title',
            'description': 'Video description'
        }

        quiz_data = {
            'questions': []
        }

        url = 'https://www.youtube.com/watch?v=test123'
        quiz = view_instance._create_quiz(
            test_user, url, video_info, quiz_data)

        assert quiz.title == 'Video Title'

    def test_create_quiz_truncates_long_description(self, view_instance, test_user):
        """
        Test quiz creation truncates description to 150 characters.

        Expects:
        - Description limited to 150 characters
        """
        video_info = {
            'title': 'Video Title',
            'description': 'Short description'
        }

        long_description = 'A' * 200
        quiz_data = {
            'description': long_description,
            'questions': []
        }

        url = 'https://www.youtube.com/watch?v=test123'
        quiz = view_instance._create_quiz(
            test_user, url, video_info, quiz_data)

        assert len(quiz.description) == 150

    # ===== ERROR DETECTION =====

    def test_is_rate_limit_error_with_429(self, view_instance):
        """
        Test detection of 429 rate limit error.

        Expects:
        - Returns True for 429 error
        """
        error_msg = "HTTP Error 429: Too Many Requests"

        result = view_instance._is_rate_limit_error(error_msg)

        assert result is True

    def test_is_rate_limit_error_with_resource_exhausted(self, view_instance):
        """
        Test detection of RESOURCE_EXHAUSTED error.

        Expects:
        - Returns True for RESOURCE_EXHAUSTED
        """
        error_msg = "RESOURCE_EXHAUSTED: Quota exceeded"

        result = view_instance._is_rate_limit_error(error_msg)

        assert result is True

    def test_is_rate_limit_error_with_other_error(self, view_instance):
        """
        Test detection returns False for non-rate-limit errors.

        Expects:
        - Returns False
        """
        error_msg = "Connection timeout"

        result = view_instance._is_rate_limit_error(error_msg)

        assert result is False

    # ===== AI PROMPT BUILDING =====

    def test_build_ai_prompt(self, view_instance):
        """
        Test AI prompt building.

        Expects:
        - Prompt contains transcript
        - Prompt contains instructions
        """
        transcript = "This is a test transcript about Python programming."

        prompt = view_instance._build_ai_prompt(transcript)

        assert 'Python programming' in prompt
        assert 'JSON' in prompt
        assert 'exactly 10 questions' in prompt
        assert 'question_title' in prompt

    def test_build_ai_prompt_truncates_long_transcript(self, view_instance):
        """
        Test that long transcripts are truncated to 3000 characters.

        Expects:
        - Transcript limited in prompt
        """
        transcript = 'A' * 5000

        prompt = view_instance._build_ai_prompt(transcript)

        # Check that transcript is truncated (prompt has more than just transcript)
        assert len(prompt) < 6000

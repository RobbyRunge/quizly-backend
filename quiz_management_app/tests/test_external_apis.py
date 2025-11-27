import pytest
from unittest.mock import patch, MagicMock

from quiz_management_app.api.views import CreateQuizView


class TestCreateQuizViewExternalAPIs:
    """
    Test suite for CreateQuizView methods that interact with external APIs.

    Tests cover:
    - YouTube video info extraction
    - Audio download
    - Audio transcription
    - AI question generation with retries
    """

    # ===== EXTRACT VIDEO INFO =====

    @patch('yt_dlp.YoutubeDL')
    def test_extract_video_info_success(self, mock_ydl_class, view_instance):
        """
        Test successful video info extraction.

        Expects:
        - Returns sanitized video info
        """
        mock_ydl = MagicMock()
        mock_info = {'title': 'Test Video', 'description': 'Test description'}
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl.sanitize_info.return_value = mock_info
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        url = 'https://www.youtube.com/watch?v=test123'
        result = view_instance._extract_video_info(url)

        assert result == mock_info
        mock_ydl.extract_info.assert_called_once_with(url, download=False)

    @patch('yt_dlp.YoutubeDL')
    def test_extract_video_info_failure(self, mock_ydl_class, view_instance):
        """
        Test video info extraction handles errors.

        Expects:
        - Returns None on exception
        """
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = Exception("Video not available")
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        url = 'https://www.youtube.com/watch?v=invalid'
        result = view_instance._extract_video_info(url)

        assert result is None

    # ===== DOWNLOAD AUDIO =====

    @patch('yt_dlp.YoutubeDL')
    def test_download_audio_success(self, mock_ydl_class, view_instance):
        """
        Test successful audio download.

        Expects:
        - Returns audio filename
        - Calls download with correct options
        """
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        url = 'https://www.youtube.com/watch?v=test123'
        result = view_instance._download_audio(url)

        assert result == 'temp_audio.mp3'
        mock_ydl.download.assert_called_once_with([url])

    # ===== TRANSCRIBE AUDIO =====

    @patch('whisper.load_model')
    def test_transcribe_audio_success(self, mock_load_model, view_instance):
        """
        Test successful audio transcription.

        Expects:
        - Returns transcript text
        """
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'text': 'This is a transcript'}
        mock_load_model.return_value = mock_model

        audio_path = 'test_audio.mp3'
        result = view_instance._transcribe_audio(audio_path)

        assert result == 'This is a transcript'
        mock_load_model.assert_called_once_with('turbo')
        mock_model.transcribe.assert_called_once_with(audio_path)

    @patch('whisper.load_model')
    def test_transcribe_audio_failure(self, mock_load_model, view_instance):
        """
        Test transcription handles errors.

        Expects:
        - Returns None on exception
        """
        mock_load_model.side_effect = Exception("Whisper error")

        audio_path = 'test_audio.mp3'
        result = view_instance._transcribe_audio(audio_path)

        assert result is None

    # ===== AI QUESTION GENERATION =====

    @patch('quiz_management_app.api.views.gemini_client')
    def test_generate_questions_success(self, mock_gemini, view_instance):
        """
        Test successful AI question generation.

        Expects:
        - Returns parsed quiz data
        """
        mock_response = MagicMock()
        mock_response.text = '{"questions": [{"question_title": "Test?", "question_options": ["A", "B"], "answer": "A"}]}'
        mock_gemini.models.generate_content.return_value = mock_response

        transcript = "Test transcript"
        result = view_instance._generate_questions_with_ai(transcript)

        assert result is not None
        assert 'questions' in result

    @patch('quiz_management_app.api.views.gemini_client')
    @patch('time.sleep')
    def test_generate_questions_retry_on_rate_limit(
        self,
        mock_sleep,
        mock_gemini,
        view_instance
    ):
        """
        Test AI generation retries on rate limit then succeeds.

        Expects:
        - Retries once with sleep
        - Returns result on second attempt
        """
        mock_response = MagicMock()
        mock_response.text = '{"questions": [{"question_title": "Test?", "question_options": ["A", "B"], "answer": "A"}]}'

        # First call raises rate limit, second succeeds
        mock_gemini.models.generate_content.side_effect = [
            Exception("429 RESOURCE_EXHAUSTED"),
            mock_response
        ]

        transcript = "Test transcript"
        result = view_instance._generate_questions_with_ai(transcript)

        assert result is not None
        assert 'questions' in result
        assert mock_gemini.models.generate_content.call_count == 2
        mock_sleep.assert_called_once_with(15)

    @patch('quiz_management_app.api.views.gemini_client')
    @patch('time.sleep')
    def test_generate_questions_rate_limit_exhausted(
        self,
        mock_sleep,
        mock_gemini,
        view_instance
    ):
        """
        Test AI generation returns RATE_LIMIT after all retries.

        Expects:
        - Returns 'RATE_LIMIT' string
        """
        mock_gemini.models.generate_content.side_effect = Exception(
            "429 Too Many Requests")

        transcript = "Test transcript"
        result = view_instance._generate_questions_with_ai(transcript)

        assert result == 'RATE_LIMIT'
        assert mock_gemini.models.generate_content.call_count == 2

    @patch('quiz_management_app.api.views.gemini_client')
    def test_generate_questions_invalid_response(self, mock_gemini, view_instance):
        """
        Test AI generation returns None for invalid response.

        Expects:
        - Returns None when parsing fails
        """
        mock_response = MagicMock()
        mock_response.text = 'Invalid JSON response'
        mock_gemini.models.generate_content.return_value = mock_response

        transcript = "Test transcript"
        result = view_instance._generate_questions_with_ai(transcript)

        assert result is None

    @patch('quiz_management_app.api.views.gemini_client')
    def test_generate_questions_non_rate_limit_exception(self, mock_gemini, view_instance):
        """
        Test AI generation raises non-rate-limit exceptions.

        Expects:
        - Re-raises the exception
        """
        mock_gemini.models.generate_content.side_effect = Exception(
            "Network error")

        transcript = "Test transcript"

        with pytest.raises(Exception, match="Network error"):
            view_instance._generate_questions_with_ai(transcript)

    # ===== GET TRANSCRIPT =====

    @patch('os.path.exists')
    @patch('os.remove')
    @patch.object(CreateQuizView, '_download_audio')
    @patch.object(CreateQuizView, '_transcribe_audio')
    def test_get_transcript_success(
        self,
        mock_transcribe,
        mock_download,
        mock_remove,
        mock_exists,
        view_instance
    ):
        """
        Test successful transcript retrieval with cleanup.

        Expects:
        - Downloads audio
        - Transcribes audio
        - Cleans up audio file
        """
        mock_download.return_value = 'temp_audio.mp3'
        mock_transcribe.return_value = 'Test transcript'
        mock_exists.return_value = True

        url = 'https://www.youtube.com/watch?v=test123'
        result = view_instance._get_transcript(url)

        assert result == 'Test transcript'
        mock_download.assert_called_once_with(url)
        mock_transcribe.assert_called_once_with('temp_audio.mp3')
        mock_remove.assert_called_once_with('temp_audio.mp3')

    @patch('os.path.exists')
    @patch('os.remove')
    @patch.object(CreateQuizView, '_download_audio')
    @patch.object(CreateQuizView, '_transcribe_audio')
    def test_get_transcript_no_cleanup_if_file_missing(
        self,
        mock_transcribe,
        mock_download,
        mock_remove,
        mock_exists,
        view_instance
    ):
        """
        Test transcript retrieval doesn't clean up if file doesn't exist.

        Expects:
        - Doesn't call remove if file not found
        """
        mock_download.return_value = 'temp_audio.mp3'
        mock_transcribe.return_value = 'Test transcript'
        mock_exists.return_value = False

        url = 'https://www.youtube.com/watch?v=test123'
        result = view_instance._get_transcript(url)

        assert result == 'Test transcript'
        mock_remove.assert_not_called()

    # ===== DOWNLOAD ERROR HANDLING =====

    @pytest.mark.django_db
    @patch('quiz_management_app.api.views.CreateQuizView._process_quiz_creation')
    def test_post_handles_download_error(self, mock_process):
        """
        Test post method handles yt_dlp.utils.DownloadError.

        Expects:
        - Returns 400 with appropriate error message
        """
        import yt_dlp
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User

        mock_process.side_effect = yt_dlp.utils.DownloadError(
            "Video unavailable")

        user = User.objects.create_user('testuser', password='test123')
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            '/api/createQuiz/', {'url': 'https://youtube.com/watch?v=test'}, format='json')

        assert response.status_code == 400
        assert 'Invalid YouTube URL or video not available' in response.data['error']

    @pytest.mark.django_db
    @patch('quiz_management_app.api.views.CreateQuizView._process_quiz_creation')
    def test_post_handles_generic_exception(self, mock_process):
        """
        Test post method handles generic exceptions.

        Expects:
        - Returns 500 with error message
        """
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User

        mock_process.side_effect = Exception("Unexpected error")

        user = User.objects.create_user('testuser2', password='test123')
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            '/api/createQuiz/', {'url': 'https://youtube.com/watch?v=test'}, format='json')

        assert response.status_code == 500
        assert 'Failed to create quiz' in response.data['error']

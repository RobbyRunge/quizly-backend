import os
import json
import time
import yt_dlp
import whisper
from google import genai

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quiz_management_app.models import Quiz, Question
from .serializers import CreateQuizSerializer, QuizSerializer, UpdateQuizSerializer


# Configure Gemini API Client
gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))


class CreateQuizView(APIView):
    """
    API endpoint to create a new quiz from a YouTube URL.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new quiz from YouTube URL.
        """
        serializer = CreateQuizSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        youtube_url = serializer.validated_data['url']

        try:
            return self._process_quiz_creation(request.user, youtube_url)
        except yt_dlp.utils.DownloadError:
            return Response(
                {'error': 'Invalid YouTube URL or video not available.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create quiz: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_quiz_creation(self, user, youtube_url):
        """
        Process the complete quiz creation workflow.
        """
        # Validate and normalize URL
        video_id = self._extract_video_id(youtube_url)
        if not video_id:
            return Response(
                {'error': 'Invalid YouTube URL format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        normalized_url = f"https://www.youtube.com/watch?v={video_id}"

        # Get video info
        video_info = self._extract_video_info(normalized_url)
        if not video_info:
            return Response(
                {'error': 'Failed to extract video information.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Transcribe video
        transcript = self._get_transcript(youtube_url)
        if not transcript:
            return Response(
                {'error': 'Failed to transcribe video audio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate quiz data
        quiz_data = self._generate_questions_with_ai(transcript)
        if quiz_data == 'RATE_LIMIT':
            return Response(
                {
                    'error': 'API rate limit exceeded. Please try again in a few minutes.',
                    'retry_after': '60 seconds'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        if not quiz_data:
            return Response(
                {'error': 'Failed to generate quiz questions.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create and save quiz
        quiz = self._create_quiz(user, normalized_url, video_info, quiz_data)
        quiz_serializer = QuizSerializer(quiz)

        return Response(quiz_serializer.data, status=status.HTTP_201_CREATED)

    def _get_transcript(self, youtube_url):
        """
        Download audio and transcribe it.
        """
        audio_path = self._download_audio(youtube_url)
        transcript = self._transcribe_audio(audio_path)

        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return transcript

    def _create_quiz(self, user, url, video_info, quiz_data):
        """
        Create quiz and questions in database.
        """
        quiz_title = quiz_data.get(
            'title', video_info.get('title', 'Quiz from YouTube'))
        quiz_description = quiz_data.get(
            'description', video_info.get('description', ''))[:150]

        quiz = Quiz.objects.create(
            title=quiz_title,
            description=quiz_description,
            video_url=url,
            created_by=user
        )

        # Create questions
        for q_data in quiz_data.get('questions', []):
            Question.objects.create(
                quiz=quiz,
                question_title=q_data['question_title'],
                question_options=q_data['question_options'],
                answer=q_data['answer']
            )

        return quiz

    def _extract_video_id(self, url):
        """
        Extract video ID from various YouTube URL formats.
        """
        import re

        patterns = [
            r'(?:youtube\.com/watch\?v=)([\w-]+)',
            r'(?:youtu\.be/)([\w-]+)',
            r'(?:youtube\.com/embed/)([\w-]+)',
            r'(?:youtube\.com/v/)([\w-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _extract_video_info(self, url):
        """
        Extract video information using yt_dlp.
        """
        ydl_opts = {}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return ydl.sanitize_info(info)
        except Exception:
            return None

    def _download_audio(self, url):
        """
        Download audio from YouTube video.
        """
        tmp_filename = 'temp_audio.mp3'
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": tmp_filename,
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return tmp_filename

    def _transcribe_audio(self, audio_path):
        """
        Transcribe audio using Whisper.
        """
        try:
            model = whisper.load_model("turbo")
            result = model.transcribe(audio_path)
            return result["text"]
        except Exception:
            return None

    def _generate_questions_with_ai(self, transcript):
        """
        Generate quiz questions from transcript using Gemini API.
        """
        prompt = self._build_ai_prompt(transcript)

        for attempt in range(2):  # max_retries = 2
            try:
                response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )

                result = self._parse_ai_response(response.text)
                if result:
                    return result

            except Exception as e:
                if self._is_rate_limit_error(str(e)):
                    if attempt < 1:  # Not last attempt
                        time.sleep(15)
                        continue
                    return 'RATE_LIMIT'
                raise e

        return None

    def _build_ai_prompt(self, transcript):
        """Build the prompt for AI question generation."""
        return f"""
            Based on the following transcript, generate a quiz in valid JSON format.

            The quiz must follow this exact structure:

            {{
            "title": "Create a concise quiz title based on the topic of the transcript.",
            "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
            "questions": [
                {{
                "question_title": "The question goes here.",
                "question_options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "The correct answer from the above options"
                }},
                ...
                (exactly 10 questions)
            ]
            }}

            Requirements:
            - Each question must have exactly 4 distinct answer options.
            - Only one correct answer is allowed per question, and it must be present in 'question_options'.
            - The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
            - Do not include explanations, comments, or any text outside the JSON.

            Transcript:
            {transcript[:3000]}
            """

    def _parse_ai_response(self, response_text):
        """
        Parse and validate AI response.
        """
        try:
            # Clean response
            response_text = response_text.strip()

            if '```' in response_text:
                parts = response_text.split('```')
                for part in parts:
                    if part.strip().startswith('json'):
                        response_text = part[4:].strip()
                    elif part.strip() and not part.strip().startswith('json'):
                        response_text = part.strip()

            result = json.loads(response_text)

            # Validate structure
            if 'questions' not in result:
                return None

            return result

        except json.JSONDecodeError:
            return None

    def _is_rate_limit_error(self, error_msg):
        """
        Check if error is a rate limit error.
        """
        return '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg


class ListQuizView(APIView):
    """
    API endpoint to list all quizzes created by the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        List all quizzes for the authenticated user.
        """
        quizzes = Quiz.objects.filter(created_by=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuizDetailView(APIView):
    """
    API endpoint to retrieve a single quiz by ID.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Retrieve a single quiz by ID.

        Returns:
        - 200: Quiz successfully retrieved
        - 401: Not authenticated
        - 403: Access denied - Quiz does not belong to user
        - 404: Quiz not found
        """
        try:
            quiz = Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            return Response(
                {'error': 'Quiz not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if quiz belongs to authenticated user
        if quiz.created_by != request.user:
            return Response(
                {'error': 'Access denied - Quiz does not belong to you.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Partially update a quiz by ID.

        Returns:
        - 200: Quiz successfully updated
        - 400: Invalid request data
        - 401: Not authenticated
        - 403: Access denied - Quiz does not belong to user
        - 404: Quiz not found
        """
        try:
            quiz = Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            return Response(
                {'error': 'Quiz not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if quiz belongs to authenticated user
        if quiz.created_by != request.user:
            return Response(
                {'error': 'Access denied - Quiz does not belong to you.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and update quiz
        serializer = UpdateQuizSerializer(
            quiz, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        # Return full quiz data with questions
        quiz_serializer = QuizSerializer(quiz)
        return Response(quiz_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """
        Delete a quiz and all associated questions permanently.

        Returns:
        - 204: Quiz successfully deleted
        - 401: Not authenticated
        - 403: Access denied - Quiz does not belong to user
        - 404: Quiz not found
        - 500: Internal server error
        """
        try:
            quiz = Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            return Response(
                {'error': 'Quiz not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if quiz belongs to authenticated user
        if quiz.created_by != request.user:
            return Response(
                {'error': 'Access denied - Quiz does not belong to you.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Delete the quiz (associated questions will be deleted via CASCADE)
            quiz.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': f'Failed to delete quiz: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

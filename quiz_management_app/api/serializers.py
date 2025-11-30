from rest_framework import serializers

from quiz_management_app.models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Question model.
    """
    class Meta:
        model = Question
        fields = [
            'id',
            'question_title',
            'question_options',
            'answer',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for Quiz model with nested questions.
    """
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'updated_at',
            'video_url',
            'questions'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UpdateQuizSerializer(serializers.ModelSerializer):
    """
    Serializer for partial updates to Quiz model.
    """
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, max_length=255)

    class Meta:
        model = Quiz
        fields = [
            'title',
            'description'
        ]


class CreateQuizSerializer(serializers.Serializer):
    """
    Serializer for quiz creation from YouTube URL.
    """
    url = serializers.URLField(required=True)

    def validate_url(self, value):
        """
        Validate that the URL is a valid YouTube URL.
        """
        if 'youtube.com' not in value and 'youtu.be' not in value:
            raise serializers.ValidationError(
                "Please provide a valid YouTube URL."
            )
        return value

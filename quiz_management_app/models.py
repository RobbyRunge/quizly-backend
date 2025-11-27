from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    """
    Quiz model representing a quiz generated from a YouTube video.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=150)
    video_url = models.URLField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Question model representing a multiple-choice question in a quiz.
    """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_title = models.CharField(max_length=500)
    question_options = models.JSONField()
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['id']

    def __str__(self):
        return f"{self.quiz.title} - {self.question_title[:50]}"

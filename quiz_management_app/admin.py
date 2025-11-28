from django.contrib import admin
from .models import Quiz, Question


class QuestionInline(admin.TabularInline):
    """
    Inline admin for Question model.
    """
    model = Question
    extra = 0
    fields = ('question_title', 'answer')
    readonly_fields = ('question_title', 'question_options', 'answer')
    can_delete = False


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """
    Admin interface for Quiz model.
    """
    list_display = (
        'title',
        'created_by',
        'created_at',
        'question_count'
    )
    list_filter = ('created_at', 'created_by')
    search_fields = ('title', 'description', 'video_url')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for Question model.
    """
    list_display = (
        'question_title_short',
        'quiz',
        'created_at'
    )
    list_filter = ('quiz', 'created_at')
    search_fields = ('question_title', 'quiz__title')
    readonly_fields = ('created_at', 'updated_at')

    def question_title_short(self, obj):
        return obj.question_title[:50] + '...' if len(
            obj.question_title
        ) > 50 else obj.question_title
    question_title_short.short_description = 'Question'

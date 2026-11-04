from django.contrib import admin

from .models import (Attempt, Question, SpeakingAttempt, SpeakingTask, Test, UserProfile,
                     Word, WritingAttempt, WritingTask)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "duration_minutes", "is_active")
    list_filter = ("section", "is_active")
    inlines = [QuestionInline]

    class Media:
        js = ("mock/admin_test.js",)


@admin.register(SpeakingTask)
class SpeakingTaskAdmin(admin.ModelAdmin):
    list_display = ("part", "prompt")
    list_filter = ("part",)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("word", "translation_uz", "part_of_speech", "band_level")
    search_fields = ("word", "translation_uz")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "test", "correct", "total", "band", "cefr", "finished_at")
    list_filter = ("test__section",)


@admin.register(SpeakingAttempt)
class SpeakingAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "band", "cefr", "created_at")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "results_consent")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")


@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ("part", "title", "duration_minutes", "minimum_words", "is_active")
    list_filter = ("part", "is_active")


@admin.register(WritingAttempt)
class WritingAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "word_count", "created_at")
    list_filter = ("task__part",)
    search_fields = ("user__username", "task__title", "response")
    readonly_fields = ("user", "task", "response", "word_count", "created_at")

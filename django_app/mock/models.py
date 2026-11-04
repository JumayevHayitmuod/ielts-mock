import re

from django.conf import settings
from django.db import models


class Section(models.TextChoices):
    READING = "reading", "Reading"
    LISTENING = "listening", "Listening"
    QUIZ = "quiz", "Quiz"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


class Test(models.Model):
    title = models.CharField(max_length=200)
    section = models.CharField(max_length=10, choices=Section.choices)
    duration_minutes = models.PositiveIntegerField(default=50)
    passage_title = models.CharField(max_length=200, blank=True)
    passage_text = models.TextField(blank=True, help_text="Reading passage. A blank line starts a new paragraph.")
    audio = models.FileField(upload_to="audio/", blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_section_display()}: {self.title}"


class Question(models.Model):
    class Kind(models.TextChoices):
        TFNG = "tfng", "True / False / Not Given"
        MCQ = "mcq", "Multiple choice"
        GAP = "gap", "Gap fill"

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    number = models.PositiveIntegerField()
    kind = models.CharField(max_length=4, choices=Kind.choices)
    instruction = models.CharField(max_length=300, blank=True, help_text="Shown above the first question of a group.")
    text = models.CharField(max_length=500)
    options = models.JSONField(default=list, blank=True, help_text='Multiple choice only, e.g. ["A", "B", "C"]')
    answer = models.CharField(max_length=200, help_text="Gap fill: separate accepted answers with |")

    class Meta:
        ordering = ["number"]
        unique_together = ("test", "number")

    def __str__(self):
        return f"Q{self.number}"

    def is_correct(self, value: str) -> bool:
        value = normalize(value)
        if not value:
            return False
        accepted = [normalize(a) for a in self.answer.split("|")]
        return value in accepted


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    exam_session = models.CharField(max_length=32, blank=True, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    correct = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    band = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    cefr = models.CharField(max_length=2, blank=True)

    class Meta:
        ordering = ["-finished_at", "-started_at"]


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.CharField(max_length=300, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["question__number"]


class SpeakingTask(models.Model):
    part = models.PositiveSmallIntegerField(choices=[(1, "Part 1"), (2, "Part 2"), (3, "Part 3")])
    prompt = models.TextField()
    bullets = models.TextField(blank=True, help_text="One cue-card bullet per line (Part 2).")
    closing = models.CharField(max_length=300, blank=True, help_text="e.g. and explain why...")
    speak_seconds = models.PositiveIntegerField(default=120)

    def __str__(self):
        return f"Part {self.part}: {self.prompt[:50]}"

    @property
    def bullet_list(self):
        return [b.strip() for b in self.bullets.splitlines() if b.strip()]


class SpeakingAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(SpeakingTask, on_delete=models.CASCADE)
    transcript = models.TextField(blank=True)
    audio = models.FileField(upload_to="speaking/", blank=True)
    fluency = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    vocabulary = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    grammar = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    pronunciation = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    band = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    cefr = models.CharField(max_length=2, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    improvements = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class WritingTask(models.Model):
    part = models.PositiveSmallIntegerField(choices=[(1, "Task 1"), (2, "Task 2")])
    title = models.CharField(max_length=200)
    prompt = models.TextField()
    data_table = models.JSONField(default=dict, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=20)
    minimum_words = models.PositiveSmallIntegerField(default=150)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Writing Task {self.part}: {self.title}"


class WritingAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(WritingTask, on_delete=models.CASCADE)
    response = models.TextField()
    word_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Word(models.Model):
    word = models.CharField(max_length=80, unique=True)
    translation_uz = models.CharField(max_length=200, blank=True)
    phonetic = models.CharField(max_length=80, blank=True)
    part_of_speech = models.CharField(max_length=30, blank=True)
    definition = models.CharField(max_length=300)
    example = models.CharField(max_length=300, blank=True)
    band_level = models.PositiveSmallIntegerField(default=7)
    wrong_options = models.JSONField(default=list, help_text="Three wrong definitions.")

    def __str__(self):
        return self.word


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=32, blank=True)
    results_consent = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()

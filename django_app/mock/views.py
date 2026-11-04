import random
import uuid
from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import services
from .forms import SignupForm
from .models import (Attempt, AttemptAnswer, Section, SpeakingAttempt, SpeakingTask, Test,
                     UserProfile, Word, WritingAttempt, WritingTask)

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
QUIZ_QUESTION_LIMIT = 10
FULL_EXAM_SESSION_KEY = "full_exam_state"
FULL_EXAM_SECTION_SECONDS = 25 * 60
CEFR_NAMES = {"A1": "Beginner", "A2": "Elementary", "B1": "Intermediate",
              "B2": "Upper-intermediate", "C1": "Advanced", "C2": "Proficient"}


def _dec(value):
    return Decimal(str(value))


def _estimate_cefr(correct, total):
    if total <= 0:
        return ""
    ratio = correct / total
    if ratio >= 0.95:
        return "C2"
    if ratio >= 0.85:
        return "C1"
    if ratio >= 0.70:
        return "B2"
    if ratio >= 0.55:
        return "B1"
    if ratio >= 0.35:
        return "A2"
    return "A1"


def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.email = form.cleaned_data["email"]
        user.save()
        UserProfile.objects.create(
            user=user,
            phone=form.cleaned_data["phone"],
            results_consent=form.cleaned_data["results_consent"],
        )
        login(request, user)
        return redirect("home")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def home(request):
    return render(request, "mock/home.html", {
        "tasks": SpeakingTask.objects.all(),
        "writing_task_count": WritingTask.objects.filter(is_active=True).count(),
        "word_count": Word.objects.count(),
        "test_count": Test.objects.filter(is_active=True).count(),
    })


@login_required
def test_catalog(request):
    reading = Test.objects.filter(section=Section.READING, is_active=True).first()
    listening = Test.objects.filter(section=Section.LISTENING, is_active=True).first()
    return render(request, "mock/tests.html", {
        "reading": Test.objects.filter(section=Section.READING, is_active=True),
        "listening": Test.objects.filter(section=Section.LISTENING, is_active=True),
        "quizzes": Test.objects.filter(section=Section.QUIZ, is_active=True),
        "full_exam_ready": bool(
            reading and reading.questions.exists()
            and listening and listening.audio and listening.questions.exists()
        ),
    })


@login_required
def test_details(request, pk):
    test = get_object_or_404(Test, pk=pk, is_active=True)
    return render(request, "mock/test_details.html", {
        "test": test,
        "question_count": test.questions.count(),
    })


@login_required
def take_test(request, pk):
    test = get_object_or_404(Test, pk=pk, is_active=True)
    session_key = f"quiz_question_ids_{test.pk}"

    if request.method == "POST":
        if test.section == Section.QUIZ:
            selected_ids = request.session.pop(session_key, None)
            if selected_ids is None:
                messages.info(request, "Start the quiz before submitting it.")
                return redirect("test", pk=test.pk)
            question_map = {q.pk: q for q in test.questions.filter(pk__in=selected_ids)}
            questions = [question_map[qid] for qid in selected_ids if qid in question_map]
        else:
            questions = list(test.questions.all())
        attempt = Attempt.objects.create(user=request.user, test=test, total=len(questions))
        answers, correct = [], 0
        for q in questions:
            value = request.POST.get(f"q{q.number}", "").strip()[:300]
            ok = q.is_correct(value)
            correct += ok
            answers.append(AttemptAnswer(attempt=attempt, question=q, value=value, is_correct=ok))
        AttemptAnswer.objects.bulk_create(answers)
        attempt.correct = correct
        attempt.finished_at = timezone.now()
        data = services.score_objective(test.section, correct, len(questions)) \
            if questions and test.section in (Section.READING, Section.LISTENING) else None
        if data:
            attempt.band, attempt.cefr = _dec(data["band"]), data["cefr"]
        else:
            attempt.cefr = _estimate_cefr(correct, len(questions))
            if test.section != Section.QUIZ:
                messages.warning(request, "Scoring service is unavailable. A practice level was estimated from your answers.")
        attempt.save()
        return redirect("results")

    if test.section == Section.QUIZ:
        selected_ids = request.session.get(session_key)
        if selected_ids is None:
            pool = list(test.questions.all())
            questions = random.sample(pool, min(QUIZ_QUESTION_LIMIT, len(pool)))
            selected_ids = [q.pk for q in questions]
            request.session[session_key] = selected_ids
        else:
            question_map = {q.pk: q for q in test.questions.filter(pk__in=selected_ids)}
            questions = [question_map[qid] for qid in selected_ids if qid in question_map]
    else:
        questions = list(test.questions.all())

    paragraphs = [p.strip() for p in test.passage_text.split("\n\n") if p.strip()]
    return render(request, "mock/test.html", {
        "test": test, "questions": questions, "paragraphs": paragraphs,
        "seconds": test.duration_minutes * 60,
    })


@login_required
def full_exam(request):
    state = request.session.get(FULL_EXAM_SESSION_KEY)
    if request.method == "POST":
        if not state:
            messages.info(request, "Full testni qaytadan boshlang.")
            return redirect("test_catalog")

        section = state["stage"]
        test = get_object_or_404(Test, pk=state[f"{section}_test_id"], is_active=True)
        question_ids = state[f"{section}_question_ids"]
        question_map = {q.pk: q for q in test.questions.filter(pk__in=question_ids)}
        questions = [question_map[qid] for qid in question_ids if qid in question_map]
        attempt = Attempt.objects.create(
            user=request.user,
            test=test,
            exam_session=state["exam_session"],
            total=len(questions),
        )
        answers, correct = [], 0
        for question in questions:
            value = request.POST.get(f"q{question.number}", "").strip()[:300]
            is_correct = question.is_correct(value)
            correct += is_correct
            answers.append(AttemptAnswer(
                attempt=attempt, question=question, value=value, is_correct=is_correct,
            ))
        AttemptAnswer.objects.bulk_create(answers)
        attempt.correct = correct
        attempt.finished_at = timezone.now()
        score = services.score_objective(section, correct, len(questions)) if questions else None
        if score:
            attempt.band, attempt.cefr = _dec(score["band"]), score["cefr"]
        else:
            attempt.cefr = _estimate_cefr(correct, len(questions))
        attempt.save()

        if section == Section.READING:
            state["stage"] = Section.LISTENING
            state["stage_started_at"] = timezone.now().timestamp()
            request.session[FULL_EXAM_SESSION_KEY] = state
            messages.success(request, "Reading tugadi. Endi Listening boshlanadi.")
            return redirect("full_exam")

        request.session.pop(FULL_EXAM_SESSION_KEY, None)
        return redirect("results")

    if not state:
        reading = Test.objects.filter(section=Section.READING, is_active=True).first()
        listening = Test.objects.filter(section=Section.LISTENING, is_active=True).first()
        if not reading or not reading.questions.exists():
            messages.info(request, "Full test uchun faol Reading testi kerak.")
            return redirect("test_catalog")
        if not listening or not listening.audio or not listening.questions.exists():
            messages.info(request, "Full test uchun audio va savollari bor faol Listening testi kerak.")
            return redirect("test_catalog")
        state = {
            "exam_session": uuid.uuid4().hex,
            "reading_test_id": reading.pk,
            "reading_question_ids": list(reading.questions.values_list("pk", flat=True)),
            "listening_test_id": listening.pk,
            "listening_question_ids": list(listening.questions.values_list("pk", flat=True)),
            "stage": Section.READING,
            "stage_started_at": timezone.now().timestamp(),
        }
        request.session[FULL_EXAM_SESSION_KEY] = state

    section = state["stage"]
    test = get_object_or_404(Test, pk=state[f"{section}_test_id"], is_active=True)
    question_ids = state[f"{section}_question_ids"]
    question_map = {q.pk: q for q in test.questions.filter(pk__in=question_ids)}
    questions = [question_map[qid] for qid in question_ids if qid in question_map]
    elapsed = int(timezone.now().timestamp() - state["stage_started_at"])
    seconds = max(FULL_EXAM_SECTION_SECONDS - elapsed, 0)
    return render(request, "mock/test.html", {
        "test": test,
        "questions": questions,
        "paragraphs": [],
        "seconds": seconds,
        "full_exam": True,
    })


@login_required
def review(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_related("test"), pk=pk, user=request.user)
    return render(request, "mock/review.html", {
        "attempt": attempt, "answers": attempt.answers.select_related("question"),
    })


@login_required
def speaking(request, pk=None):
    task = get_object_or_404(SpeakingTask, pk=pk) if pk else SpeakingTask.objects.filter(part=2).first() \
        or SpeakingTask.objects.first()
    if task is None:
        messages.info(request, "No speaking tasks yet. Add one in the admin.")
        return redirect("home")

    if request.method == "POST":
        transcript = request.POST.get("transcript", "").strip()[:8000]
        sa = SpeakingAttempt(user=request.user, task=task, transcript=transcript)
        if request.FILES.get("audio"):
            sa.audio = request.FILES["audio"]
        data = services.evaluate_speaking(task.prompt, transcript) if transcript else None
        if data:
            for key in ("fluency", "vocabulary", "grammar", "pronunciation", "band"):
                setattr(sa, key, _dec(data[key]))
            sa.cefr = data["cefr"]
            sa.strengths, sa.improvements = data["strengths"], data["improvements"]
        else:
            messages.warning(request, "Could not score this answer. Add a transcript and make sure the scoring service is running.")
        sa.save()
        return redirect("results")

    return render(request, "mock/speaking.html", {"task": task, "tasks": SpeakingTask.objects.all()})


@login_required
def writing(request, pk=None):
    tasks = WritingTask.objects.filter(is_active=True).order_by("part", "pk")
    if pk is None:
        return render(request, "mock/writing.html", {"tasks": tasks})

    task = get_object_or_404(tasks, pk=pk)
    if request.method == "POST":
        response_text = request.POST.get("response", "").strip()[:20000]
        if not response_text:
            messages.error(request, "Javob matnini kiriting.")
            return render(request, "mock/writing_task.html", {"task": task})
        attempt = WritingAttempt.objects.create(
            user=request.user,
            task=task,
            response=response_text,
            word_count=len(response_text.split()),
        )
        return redirect("writing_result", pk=attempt.pk)
    return render(request, "mock/writing_task.html", {"task": task})


@login_required
def writing_result(request, pk):
    attempt = get_object_or_404(
        WritingAttempt.objects.select_related("task"), pk=pk, user=request.user,
    )
    return render(request, "mock/writing_result.html", {"attempt": attempt})


@login_required
def resources(request):
    return render(request, "mock/resources.html")


@login_required
def vocabulary(request):
    return render(request, "mock/vocabulary.html", {
        "words": Word.objects.all().order_by("word"),
    })


@login_required
def vocabulary_test(request):
    feedback = None
    if request.method == "POST":
        word = get_object_or_404(Word, pk=request.POST.get("word_id"))
        feedback = {"correct": request.POST.get("choice") == word.definition}
        options = []
    else:
        words = list(Word.objects.all())
        if not words:
            messages.info(request, "No words yet. Add some in the admin.")
            return redirect("home")
        last = request.GET.get("after")
        pool = [w for w in words if str(w.pk) != last] or words
        word = random.choice(pool)
        options = [word.definition] + list(word.wrong_options)[:3]
        random.shuffle(options)
    return render(request, "mock/vocabulary_test.html", {"word": word, "options": options, "feedback": feedback})


@login_required
def results(request):
    latest_attempt = Attempt.objects.filter(
        user=request.user, finished_at__isnull=False,
    ).select_related("test").first()
    latest_level = ""
    result_title = ""
    result_correct = 0
    result_total = 0
    section_results = []
    if latest_attempt:
        attempts = [latest_attempt]
        if latest_attempt.exam_session:
            attempts = list(Attempt.objects.filter(
                user=request.user,
                exam_session=latest_attempt.exam_session,
            ).select_related("test"))
        result_correct = sum(attempt.correct for attempt in attempts)
        result_total = sum(attempt.total for attempt in attempts)
        latest_level = _estimate_cefr(result_correct, result_total)
        result_title = "Reading + Listening" if len(attempts) > 1 else latest_attempt.test.title
        section_results = [{
            "name": attempt.test.get_section_display(),
            "correct": attempt.correct,
            "total": attempt.total,
        } for attempt in attempts]
    return render(request, "mock/results.html", {
        "latest_attempt": latest_attempt,
        "latest_level": latest_level,
        "latest_level_name": CEFR_NAMES.get(latest_level, ""),
        "result_title": result_title,
        "result_correct": result_correct,
        "result_total": result_total,
        "section_results": section_results,
    })

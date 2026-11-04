from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from unittest.mock import patch

from .models import (Attempt, Question, Section, Test as IELTSPracticeTest, Word,
                     WritingAttempt, WritingTask)


class AccountAndPracticeTests(TestCase):
    def test_flag_language_switch_persists_between_pages(self):
        user = get_user_model().objects.create_user(username="languageuser", password="test-pass-12345")
        self.client.force_login(user)

        uz_page = self.client.get(reverse("home"))
        self.assertContains(uz_page, 'lang="uz"')
        self.assertContains(uz_page, "Sinovlarimiz")
        self.assertContains(uz_page, "🇺🇿")
        self.assertContains(uz_page, '<details class="language-menu">')
        self.assertContains(uz_page, "O‘zbekcha")
        self.assertContains(uz_page, "English")

        response = self.client.post(reverse("set_language"), {
            "language": "en",
            "next": reverse("home"),
        })
        self.assertRedirects(response, reverse("home"))
        en_page = self.client.get(reverse("home"))
        self.assertContains(en_page, 'lang="en"')
        self.assertContains(en_page, "Practice tests")
        self.assertNotContains(en_page, "Sinovlarimiz")
        self.assertContains(en_page, "🇬🇧")
        self.assertContains(self.client.get(reverse("resources")), "IELTS preparation resources")
        self.assertNotContains(self.client.get(reverse("resources")), "IELTS tayyorgarlik manbalari")
        Word.objects.create(word="hello", definition="a greeting", translation_uz="salom")
        self.assertContains(self.client.get(reverse("vocabulary")), "Uzbek translation:")
        self.assertNotContains(self.client.get(reverse("vocabulary")), "O‘zbekcha tarjima:")

        self.client.post(reverse("set_language"), {
            "language": "uz",
            "next": reverse("home"),
        })
        self.assertContains(self.client.get(reverse("home")), "Sinovlarimiz")
        self.assertContains(self.client.get(reverse("vocabulary")), "O‘zbekcha tarjima:")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_email_can_set_a_new_password(self):
        user = get_user_model().objects.create_user(
            username="resetuser", email="reset@example.com", password="old-pass-12345",
        )

        response = self.client.post(reverse("password_reset"), {"email": user.email})

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Parolni tiklash uchun quyidagi havolani oching", mail.outbox[0].body)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_url = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 302)
        set_password_url = response["Location"]
        self.assertContains(self.client.get(set_password_url), "Yangi parol o‘rnating")

        response = self.client.post(set_password_url, {
            "new_password1": "new-secure-pass-54321",
            "new_password2": "new-secure-pass-54321",
        })

        self.assertRedirects(response, reverse("password_reset_complete"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("new-secure-pass-54321"))

    def test_signup_saves_profile_and_logs_user_in(self):
        response = self.client.post(reverse("signup"), {
            "username": "learner1",
            "first_name": "Amina",
            "last_name": "Example",
            "email": "amina@example.com",
            "email_confirm": "amina@example.com",
            "phone": "+998901234567",
            "password1": "Good-password-482!",
            "password2": "Good-password-482!",
            "results_consent": "on",
        })

        self.assertRedirects(response, reverse("home"))
        user = get_user_model().objects.get(username="learner1")
        self.assertEqual(user.get_full_name(), "Amina Example")
        self.assertEqual(user.email, "amina@example.com")
        self.assertEqual(user.profile.phone, "+998901234567")
        self.assertTrue(user.profile.results_consent)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_reading_shows_25_minute_timer_and_one_question(self):
        user = get_user_model().objects.create_user(username="reader", password="test-pass-12345")
        test = IELTSPracticeTest.objects.create(
            title="Reading practice", section=Section.READING, duration_minutes=25,
            passage_title="Hidden reading text", passage_text="This passage should not be shown.",
        )
        Question.objects.create(
            test=test, number=1, kind=Question.Kind.MCQ, text="Choose the answer",
            options=["A", "B"], answer="A",
        )
        Question.objects.create(
            test=test, number=2, kind=Question.Kind.MCQ, text="Choose another answer",
            options=["C", "D"], answer="C",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("test", args=[test.pk]))

        self.assertContains(response, 'data-seconds="1500"')
        self.assertContains(response, 'name="language" value="en"')
        self.assertContains(response, "Choose the answer")
        self.assertNotContains(response, "This passage should not be shown.")
        self.assertNotContains(response, "Hidden reading text")
        self.assertContains(response, 'id="next-question"')
        self.assertContains(response, "Savol 1 / 2")
        self.assertContains(response, 'id="q2" hidden')
        details = self.client.get(reverse("test_details", args=[test.pk]))
        self.assertContains(details, "25")
        self.assertContains(details, "Testni topshirish")

    def test_quiz_attempt_is_saved_to_current_user(self):
        user = get_user_model().objects.create_user(username="quizzer", password="test-pass-12345")
        test = IELTSPracticeTest.objects.create(
            title="Vocabulary quiz", section=Section.QUIZ, duration_minutes=25,
        )
        question = Question.objects.create(
            test=test, number=1, kind=Question.Kind.MCQ, text="Choose the answer",
            options=["Correct", "Incorrect"], answer="Correct",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("test", args=[test.pk]))
        self.assertContains(response, 'data-seconds="1500"')

        response = self.client.post(reverse("test", args=[test.pk]), {"q1": "Correct"})

        self.assertRedirects(response, reverse("results"))
        attempt = Attempt.objects.get(test=test)
        self.assertEqual(attempt.user, user)
        self.assertEqual(attempt.correct, 1)
        self.assertEqual(attempt.total, 1)
        self.assertEqual(attempt.answers.get(question=question).value, "Correct")
        results = self.client.get(reverse("results"))
        self.assertContains(results, "Vocabulary quiz")
        self.assertContains(results, "1/1")
        self.assertContains(results, "C2")

    def test_quiz_randomly_selects_ten_and_hides_total(self):
        user = get_user_model().objects.create_user(username="randomquiz", password="test-pass-12345")
        test = IELTSPracticeTest.objects.create(
            title="Random quiz", section=Section.QUIZ, duration_minutes=25,
        )
        questions = [Question.objects.create(
            test=test,
            number=number,
            kind=Question.Kind.MCQ,
            text=f"Choose word {number} for the ______.",
            options=["one", "two", "three", "four"],
            answer="one",
        ) for number in range(1, 13)]
        self.client.force_login(user)

        with patch("mock.views.random.sample", side_effect=[questions[:10], questions[2:]]) as sampler:
            response = self.client.get(reverse("test", args=[test.pk]))
            first_ids = [question.pk for question in response.context["questions"]]
            self.assertEqual(len(first_ids), 10)
            self.assertTrue(all(len(question.options) == 4 for question in response.context["questions"]))
            self.assertNotContains(response, "of 10")

            refreshed = self.client.get(reverse("test", args=[test.pk]))
            self.assertEqual([q.pk for q in refreshed.context["questions"]], first_ids)
            self.assertEqual(sampler.call_count, 1)

            self.client.post(reverse("test", args=[test.pk]), {
                f"q{question.number}": question.answer for question in response.context["questions"]
            })
            self.assertEqual(Attempt.objects.get(test=test).total, 10)

            next_attempt = self.client.get(reverse("test", args=[test.pk]))
            self.assertEqual([q.pk for q in next_attempt.context["questions"]], [q.pk for q in questions[2:]])
            self.assertEqual(sampler.call_count, 2)

        self.assertNotContains(self.client.get(reverse("test_details", args=[test.pk])), "12 questions")

    def test_full_exam_moves_from_reading_to_listening_and_combines_results(self):
        user = get_user_model().objects.create_user(username="fulltest", password="test-pass-12345")
        reading = IELTSPracticeTest.objects.create(
            title="Reading section", section=Section.READING, duration_minutes=25,
        )
        Question.objects.create(
            test=reading, number=1, kind=Question.Kind.MCQ, text="Reading question ______.",
            options=["right", "wrong", "other", "none"], answer="right",
        )
        listening = IELTSPracticeTest.objects.create(
            title="Listening section", section=Section.LISTENING,
            duration_minutes=25, audio="audio/listening.mp3",
        )
        Question.objects.create(
            test=listening, number=1, kind=Question.Kind.MCQ, text="Listening question ______.",
            options=["right", "wrong", "other", "none"], answer="right",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("test_catalog"))
        self.assertContains(response, "To‘liq testni boshlash")
        response = self.client.get(reverse("full_exam"))
        self.assertContains(response, "data-seconds=\"1500\"")
        session_id = self.client.session["full_exam_state"]["exam_session"]

        response = self.client.post(reverse("full_exam"), {"q1": "right"})
        self.assertRedirects(response, reverse("full_exam"))
        self.assertEqual(self.client.session["full_exam_state"]["stage"], Section.LISTENING)
        response = self.client.get(reverse("full_exam"))
        self.assertContains(response, "Listening audio")
        self.assertContains(response, "data-seconds=\"1500\"")

        response = self.client.post(reverse("full_exam"), {"q1": "right"})
        self.assertRedirects(response, reverse("results"))
        attempts = Attempt.objects.filter(user=user, exam_session=session_id)
        self.assertEqual(attempts.count(), 2)
        results = self.client.get(reverse("results"))
        self.assertContains(results, "Reading + Listening")
        self.assertContains(results, "2/2")

    def test_writing_submission_is_saved_for_its_owner(self):
        task = WritingTask.objects.create(
            part=2,
            title="Public spaces",
            prompt="Do public spaces improve communities?",
            minimum_words=250,
        )
        writer = get_user_model().objects.create_user(username="writer", password="test-pass-12345")
        other_user = get_user_model().objects.create_user(username="otherwriter", password="test-pass-12345")
        self.client.force_login(writer)

        response = self.client.post(reverse("writing_task", args=[task.pk]), {
            "response": "Public spaces can bring people together. " * 60,
        })

        attempt = WritingAttempt.objects.get(user=writer, task=task)
        self.assertRedirects(response, reverse("writing_result", args=[attempt.pk]))
        self.assertGreaterEqual(attempt.word_count, 250)
        self.assertContains(self.client.get(reverse("writing_result", args=[attempt.pk])), "ta so‘z akkauntingizda saqlandi")

        self.client.force_login(other_user)
        self.assertEqual(self.client.get(reverse("writing_result", args=[attempt.pk])).status_code, 404)

    def test_official_resources_page_has_external_sources(self):
        user = get_user_model().objects.create_user(username="resourceuser", password="test-pass-12345")
        self.client.force_login(user)

        response = self.client.get(reverse("resources"))

        self.assertContains(response, "IELTS.org")
        self.assertContains(response, "British Council")
        self.assertContains(response, "IDP IELTS")

    def test_seeded_vocabulary_has_one_hundred_words_with_pronunciation(self):
        call_command("seed_words", verbosity=0)
        words = Word.objects.order_by("word")
        self.assertEqual(words.count(), 100)
        self.assertTrue(all(word.translation_uz for word in words))
        self.client.force_login(get_user_model().objects.create_user(
            username="vocabuser", password="test-pass-12345",
        ))

        response = self.client.get(reverse("vocabulary"))

        self.assertContains(response, "100 words")
        self.assertContains(response, "O‘zbekcha tarjima:")
        self.assertContains(response, "tashlab ketmoq")
        self.assertContains(response, "data-pronounce=")
        self.assertContains(response, "data-audio-target=")
        self.assertNotContains(response, "data-speech-rate=")
        self.assertContains(response, "audio.playbackRate=1")
        self.assertContains(response, 'utterance.rate=1.05')
        self.assertContains(response, "audio.volume=0.9")
        self.assertContains(response, "speechSynthesis")
        self.assertContains(response, "/natural|online/i")
        self.assertContains(response, "utterance.rate=1.05")
        self.assertContains(response, "utterance.volume=0.9")

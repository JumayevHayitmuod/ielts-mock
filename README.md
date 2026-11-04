# IELTS Mock Test (Django + FastAPI)

- **django_app/**: website (login, Reading, Listening, Speaking, Vocabulary, Results, admin panel, database).
- **fastapi_service/**: scoring API (raw score to band, band to CEFR, overall band, Speaking evaluation).

Django saves the data and calls FastAPI for every score. Both must be running.

## Run (two terminals)

Use the same `SCORING_API_KEY` value in both (default `dev-key` works for local development).

```bash
# 1) FastAPI, port 8001
cd fastapi_service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SCORING_API_KEY=dev-key
# optional AI speaking evaluation:
# export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --port 8001 --reload
```

```bash
# 2) Django, port 8000
cd django_app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations mock
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py seed_quiz
python manage.py seed_full_site
python manage.py seed_words
python manage.py generate_word_audio
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in or sign up. Add tests, questions, audio, speaking tasks and words in http://127.0.0.1:8000/admin.

The site interface defaults to Uzbek. Use the 🇺🇿 UZ / 🇬🇧 EN controls in the header to change languages; the selection is retained while browsing.

## Adding content

- **Reading:** create a Test (section Reading), paste the passage, add Questions inline.
- **Listening:** create a Test (section Listening), upload an audio file, add Questions, tick "is active".
- **Quiz:** create a Test (section Quiz), leave the passage fields empty, and add Questions inline.
- **Full test:** add an active Reading test and an active Listening test with audio and questions. The combined exam runs Reading for 25 minutes, then Listening for 25 minutes.
- **Speaking:** add prompts for Parts 1, 2, and 3 under Speaking Tasks.
- **Writing:** add Task 1 and Task 2 under Writing Tasks. User responses are saved to their own accounts.
- **Questions:** `tfng` (answer TRUE / FALSE / NOT GIVEN), `mcq` (options as a JSON list, answer equals one option), `gap` (answer text; several accepted answers separated by `|`).
- Use your own or properly licensed material. Do not copy Cambridge IELTS books.

Official practice resources: [IELTS sample questions](https://ielts.org/take-a-test/preparation-resources/sample-test-questions/academic-test), [British Council free practice tests](https://takeielts.britishcouncil.org/prepare/ielts-free-practice-mock-tests/academic), and [IDP IELTS preparation](https://ielts.idp.com/prepare).

## Notes

- In local development, password-reset emails are printed in the Django terminal. For real email, configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL`.
- Band tables are approximate (Academic Reading and Listening). A test with fewer than 40 questions is scaled to 40.
- Speaking uses a transcript (browser speech recognition where supported, or typed). Pronunciation cannot be judged from text, so it is only an estimate.
- Production: set `DJANGO_DEBUG=0`, a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, serve media/static properly and keep FastAPI on a private network.

## FastAPI endpoints (header `X-API-Key`)

- `POST /score/objective` `{section, correct, total}`
- `POST /score/overall` `{bands: [..]}`
- `POST /speaking/evaluate` `{prompt, transcript}`
- `GET /health`

Interactive docs at http://127.0.0.1:8001/docs

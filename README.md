# FakeNews Killer

**AI-powered misinformation detection and response for Pakistan.**

FakeNews Killer takes a WhatsApp forward, a headline, or a screenshot and runs it through a four-stage AI pipeline that extracts the claims, fact-checks them against live web sources, assesses the potential for harm, and produces ready-to-use responses: a shareable verdict card, a tracker record, and a formal platform abuse report.

It supports English, Urdu, and Roman Urdu, and it favours trusted Pakistani and international news sources.

---

## Table of contents

- [Why it exists](#why-it-exists)
- [Features](#features)
- [How it works](#how-it-works)
- [Mobile app](#mobile-app)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Deployment](#deployment)
- [Project structure](#project-structure)
- [Example](#example)
- [Design notes](#design-notes)
- [Limitations](#limitations)
- [Authors](#authors)

---

## Why it exists

Millions of people in Pakistan receive unverified news forwards every day: political rumours, health hoaxes, economic panic, and religious misinformation. By the time a journalist or fact-checker responds, the message has already spread.

Existing tools tend to:

- stop at summarising the content instead of helping anyone act on it,
- depend on manual review by journalists, which is too slow, or
- support English only, which leaves out most of the country.

FakeNews Killer addresses all three.

## Features

- **Claim extraction:** splits a message into separate claims that can each be checked.
- **Live fact-checking:** checks each claim with Google Search grounding and prefers sources such as Dawn, Geo, ARY, The Express Tribune, The News, Reuters, and AFP.
- **Multilingual:** detects and handles English, Urdu, and Roman Urdu.
- **Screenshot input:** reads the text in up to five images on the device using ML Kit text recognition.
- **Harm assessment:** rates the harm level, the affected audience, and the risk of spread, then ranks the recommended responses.
- **Actionable outputs:**
  - a WhatsApp-ready verdict card that includes a Roman Urdu warning,
  - a persistent record in the misinformation tracker,
  - a formal abuse report drafted for WhatsApp, Facebook, or X.
- **Live progress:** the app streams each agent's progress over Server-Sent Events.
- **Resilient model access:** if a Gemini model hits a rate limit, quota, or error, the backend automatically retries with the next model in its list.

## How it works

Every request passes through four specialised agents in sequence. Each agent receives the previous agent's structured output, and Pydantic validates every stage.

```
 Text / screenshot (OCR on device)
              │
              ▼
 ┌────────────────────────┐
 │ 1. Reader              │  Detects the language, extracts discrete claims,
 │                        │  flags linguistic red flags, scores suspicion
 └───────────┬────────────┘
             ▼
 ┌────────────────────────┐
 │ 2. Analyst             │  Fact-checks each claim with Google Search,
 │    [google_search]     │  assigns a truth score (0–100), cites sources
 └───────────┬────────────┘
             ▼
 ┌────────────────────────┐
 │ 3. Strategist          │  Assesses harm, audience and spread risk,
 │                        │  plans prioritised responses
 └───────────┬────────────┘
             ▼
 ┌────────────────────────┐
 │ 4. Executor            │  Produces the verdict card, writes the tracker
 │                        │  entry, drafts the platform report
 └───────────┬────────────┘
             ▼
     JSON response / SSE stream  →  Flutter app
```

### Executor outputs

**Verdict card:** a shareable fact-check card with:

- the verdict (TRUE / FALSE / MISLEADING / UNVERIFIED) and a confidence percentage,
- the key finding in plain language and the sources consulted,
- a Roman Urdu warning, for example *"⚠️ Yeh khabar BILKUL GALAT hai. Aagay mat bhejen."*

**Tracker entry:** a record saved to the misinformation tracker:

```json
{
  "claim_text": "...",
  "verdict": "false",
  "category": "political",
  "language": "roman_urdu",
  "spread_risk": "high",
  "sources_cited": ["Dawn.com", "Geo.tv"],
  "tags": ["election", "whatsapp-forward"],
  "status": "active",
  "confidence_score": 91
}
```

**Platform report:** a formal content abuse report covering the harm category, an evidence summary, and the recommended platform action. You can review it and submit it to WhatsApp, Facebook, or X.

**Execution log:** a timestamped record of every step:

```
[09:23:01] Reader      → 2 claims extracted
[09:23:03] Analyst     → google_search (3 queries)
[09:23:07] Analyst     → verdict: FALSE (confidence: 91%)
[09:23:08] Strategist  → 3 actions recommended
[09:23:09] Executor    → verdict card generated
[09:23:09] Executor    → tracker entry created
[09:23:10] Executor    → platform report drafted
```

## Mobile app

The client is built in Flutter. Android is the primary target.

| Screen | Purpose |
|---|---|
| **Splash** | Branding and startup |
| **Input** | Paste a message or attach up to five screenshots |
| **Loading** | A live ticker that shows each agent finishing in real time |
| **Results** | The overall verdict, the confidence score, and a breakdown for each claim |
| **Verdict Card** | A shareable card, exported as an image through the system share sheet |
| **Before / After** | What the pipeline changed, plus the full execution log |
| **Tracker** | A dashboard of past entries, their categories, and their spread risk |

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini (`google-genai` SDK), with model fallback |
| Fact-checking | Gemini Google Search grounding tool |
| Backend | FastAPI, Uvicorn, Python 3.11+ |
| Validation | Pydantic v2 |
| Database | Google Cloud Firestore |
| OCR | Google ML Kit Text Recognition (on device) |
| Mobile | Flutter (Dart ≥ 3.8) |
| Hosting | Google Cloud Run (Docker) |

## Getting started

### Prerequisites

- Python 3.11 or newer
- Flutter SDK (Dart 3.8 or newer) and an Android device or emulator
- A Google AI Studio / Gemini API key
- A Google Cloud project with Firestore enabled, plus credentials that can access it (for local development, `gcloud auth application-default login` is enough)

### 1. Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

echo "GOOGLE_API_KEY=your-gemini-api-key" > .env.local

uvicorn main:app --reload --port 8000
```

Interactive API docs are then available at <http://localhost:8000/docs>.

When the tracker collection is empty, the backend adds a few example entries on first startup so the dashboard has data to show.

### 2. Run the mobile app

The app points to the hosted Cloud Run API by default. To use your local backend instead, open `app/lib/services/api_service.dart`, comment out the production `baseUrl`, and uncomment the local development getter. On an Android emulator, that getter uses `10.0.2.2:8000`.

```bash
cd app
flutter pub get
flutter run
```

## Configuration

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | The Gemini API key that all four agents use |
| `GOOGLE_CLOUD_PROJECT` | Outside GCP | The Firestore project ID. Detected automatically on Cloud Run |
| `GOOGLE_APPLICATION_CREDENTIALS` | Outside GCP | Path to a service-account JSON file, if you don't use ADC |
| `PORT` | No | The server port inside the container (default `8080`) |

The backend loads `backend/.env.local` first and then `backend/.env`. Both files are git-ignored.

To change the order in which Gemini models are tried, edit `FALLBACK_MODELS` in `backend/utils/gemini_client.py`.

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check, returns `{"status": "ok"}` |
| `POST` | `/analyze` | Runs the full pipeline and returns one JSON response |
| `POST` | `/analyze/stream` | Runs the pipeline and streams progress as Server-Sent Events |
| `GET` | `/tracker` | Lists every tracker entry, newest first |
| `POST` | `/tracker` | Adds a tracker entry manually |

**Request body** for `/analyze` and `/analyze/stream`:

```json
{ "text": "URGENT! PM ne resign kar diya..." }
```

**Response:** an object with `reader`, `analyst`, `strategist`, and `executor` keys, one per pipeline stage. The full schemas are in `backend/models/schemas.py`, and you can also browse them at `/docs`.

**Stream events:**

```
data: {"agent": "reader",     "status": "complete"}
data: {"agent": "analyst",    "status": "complete"}
data: {"agent": "strategist", "status": "complete"}
data: {"agent": "executor",   "status": "complete"}
data: {"agent": "pipeline",   "status": "complete", "result": { ... }}
```

If a stage fails, the stream sends `{"agent": "pipeline", "status": "error", "error": "..."}`.

## Deployment

The backend ships with a `Dockerfile` for Google Cloud Run:

```bash
cd backend
gcloud run deploy fakenews-killer-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your-gemini-api-key
```

Make sure the Cloud Run service account has the **Cloud Datastore User** role so that it can read from and write to Firestore. For production, store the API key in Secret Manager and pass it with `--set-secrets` rather than as a plain environment variable.

To build a release APK of the app:

```bash
cd app
flutter build apk --release
```

## Project structure

```
fakenews-killer/
├── backend/
│   ├── main.py                 # FastAPI app and routes
│   ├── agents/
│   │   ├── reader.py           # Stage 1: language detection and claim extraction
│   │   ├── analyst.py          # Stage 2: fact-checking with Google Search
│   │   ├── strategist.py       # Stage 3: harm assessment and action planning
│   │   └── executor.py         # Stage 4: verdict card, tracker entry, report
│   ├── models/
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── database.py         # Firestore tracker persistence
│   ├── utils/
│   │   ├── gemini_client.py    # Gemini calls with model fallback
│   │   └── ocr.py              # Server-side Gemini vision OCR helper
│   ├── requirements.txt
│   └── Dockerfile
└── app/                        # Flutter client
    ├── lib/
    │   ├── main.dart
    │   ├── models/             # AnalysisResult, TrackerEntry
    │   ├── services/           # ApiService (REST + SSE)
    │   ├── screens/            # Splash, Input, Loading, Results,
    │   │                       # Verdict Card, Before/After, Tracker
    │   └── widgets/            # Shared scaffold and drawer
    ├── assets/
    └── pubspec.yaml
```

## Example

**Input (a Roman Urdu WhatsApp forward):**

```
URGENT! PM ne resign kar diya aur army ne complete control le lia hai.
Sab channels band hone wale hain. SHARE KAREIN JALDI!
```

**Result:**

| Stage | Output |
|---|---|
| Reader | 2 claims: (1) the PM resigned, (2) the army took control. Suspicion 9/10. Red flags: urgency, unnamed source, ALL CAPS |
| Analyst | Claim 1 is **FALSE** (4/100): no resignation reported by Dawn, Geo, or Tribune. Claim 2 is **FALSE** (6/100): no credible reports of military action |
| Strategist | Harm: **HIGH**. Audience: the general public. Actions: public correction (immediate), tracker log (immediate), platform flag (within 24h) |
| Executor | Verdict card generated, tracker entry created, WhatsApp report drafted |

## Design notes

- **A chain of agents instead of one prompt.** Each agent has one narrow job and a strict output schema, which gives more reliable structured output than a single large prompt.
- **Roman Urdu is fully supported.** The Reader treats `roman_urdu` as its own language, separate from English and Urdu.
- **Spread risk is a key metric.** The system records how likely a claim is to go viral, not only whether it is true.
- **A person approves before anything leaves the app.** The pipeline drafts the platform reports and prepares the verdict cards, but a person still decides to share or submit them.

## Limitations

- Verdicts are generated by AI and can be wrong. Treat them as decision support, not as a final ruling.
- Fact-checking quality depends on how much a topic has been covered online. Very recent or very local claims may come back as `UNVERIFIED`.
- On-device OCR uses the Latin-script recogniser, so text in Urdu (Nastaliq) script inside images may not be extracted reliably.
- The API has no authentication or rate limiting. Add both before you expose it publicly at scale.

## Authors

- **Muhammad Aziz**: backend, agent pipeline, Flutter app, API integration
- **Muhammad Zakir**: research, content, documentation, QA

---

*FakeNews Killer: because the truth deserves a faster distribution network than the lie.*

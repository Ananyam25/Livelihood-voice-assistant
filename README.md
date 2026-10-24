# Livelihood Assistant

> **Livelihood Assistant is a voice-first, multimodal AI solution for informal and rural workers. Powered by Gemma 4, it converts spoken experiences and work photos into structured skill profiles. It performs skill gap analysis to provide actionable micro-learning paths and job matching, using an accessible, minimal-text interface.**

---

## 🌟 What It Does

| Feature | Description |
|---|---|
| 🎙 **Voice Input** | Speak your work history in Hindi, Tamil, or English — no typing required |
| 📷 **Photo Evidence** | Upload photos of your work; Gemma 4 identifies tools and skills from the image |
| 📝 **Text Fallback** | Type or paste in any language |
| 🧠 **Skill Extraction** | Gemma 4 produces a structured Skill & Livelihood Profile from any input |
| 🎯 **Gap Analysis** | Compares your profile against real job requirements to find what you're missing |
| 📚 **Micro-learning** | Recommends 2 free/low-cost government-backed courses that close the gap |
| 💼 **Job Matching** | Ranks real job opportunities by skill overlap + experience fit |
| 🗺 **Career Pathway** | Visual 3-step roadmap: Current Skills → Skill Gap → Target Job |
| 🔊 **Read Aloud (TTS)** | Every result can be read aloud in the browser — no literacy required |
| 📊 **Readiness Score** | Composite 0–100 score reflecting how ready you are for top roles |

---

## 🏗 Architecture

```
livelihood-assistant/
├── data/
│   └── mock_database.json      ← Worker profiles, jobs, courses, skill taxonomy
├── backend/
│   ├── multimodal_gemma.py     ← Gemma 4 integration + mock fallback
│   └── career_engine.py        ← Skill gap, job matching, course recommendation
├── static/
│   ├── index.html              ← Voice-first accessible SPA
│   ├── style.css               ← Premium dark glassmorphism design system
│   └── app.js                  ← Web Speech API, TTS, API calls, UI rendering
├── app.py                      ← FastAPI server
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Install Dependencies

```bash
cd "livelihood assistant"
pip install -r requirements.txt
```

### 3. (Optional) Set Gemma 4 API Key

Without a key the app runs in **mock mode** with highly realistic pre-built profiles — perfect for demos.

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your-api-key-here"

# Linux / macOS
export GEMINI_API_KEY="your-api-key-here"
```

Get a free API key at: https://aistudio.google.com/app/apikey

### 4. Run the App

```bash
python app.py
```

Or via uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open in Browser

```
http://localhost:8000
```

---

## 🧪 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/`                        | Serves the web application |
| `POST` | `/api/analyse`             | Core endpoint – accepts voice transcript, image, text |
| `GET`  | `/api/demo?profile_type=X` | Load a pre-built demo (carpenter / weaver / hvac) |
| `GET`  | `/api/db/stats`            | Impact statistics |
| `GET`  | `/api/db/jobs`             | All job opportunities |
| `GET`  | `/docs`                    | Interactive Swagger API docs |

### POST `/api/analyse` – Form Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `text_input` | `str` | — | Typed / pasted description |
| `transcript` | `str` | — | Voice-to-text result |
| `image` | `File` | — | Work evidence photo |

At least one field must be provided.

---

## 🎭 Demo Mode

Click any demo button in the UI to instantly load a pre-built worker profile:

| Demo | Worker | Trade |
|---|---|---|
| 🪚 Rajesh | 45-year-old carpenter | 15 years woodworking experience |
| 🧵 Meena | 38-year-old master weaver | 20 years Banarasi brocade |
| ❄️ Suresh | 32-year-old HVAC technician | 10 years AC servicing |

---

## 🤖 Gemma 4 Integration

The app uses `google-generativeai` SDK with the following models:
- Default: `gemma-3-27b-it` (change via `GEMMA_MODEL` env var)
- Falls back to deterministic mock functions if no API key is present

The system prompt instructs Gemma 4 to:
1. Extract structured JSON skill profiles from any modality
2. Recognise informal knowledge as legitimate expertise
3. Return consistent schema with confidence scores

---

## ♿ Accessibility Features

- All interactive elements have ARIA labels and roles
- Full keyboard navigation (Tab, Enter, Space)
- `prefers-reduced-motion` respected
- High-contrast colour palette (WCAG AA compliant)
- Text-to-Speech (TTS) "Read Aloud" buttons throughout
- Large touch targets (min 44×44px)
- `aria-live` regions for dynamic content updates

---

## 🛠 Development

```bash
# Run with hot-reload
uvicorn app:app --reload

# Test backend logic directly
python backend/multimodal_gemma.py
python backend/career_engine.py
```

---

## 📄 Licence

MIT — Built for the 2026 Hackathon. Free to adapt for social impact.

---

*Built with ❤️ for India's 450 million informal workers.*

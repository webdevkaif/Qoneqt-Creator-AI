# Qoneqt Creator AI 🎬✨

> **AI-powered video creation platform** — transform any topic, prompt, or trend into a polished short video ready for the Qoneqt Global Feed.

![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python)
![MongoDB](https://img.shields.io/badge/MongoDB-Motor%2FBeanie-47A248?style=flat-square&logo=mongodb)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## ⚡ Quick Start — Run Locally

> **Demo Video Available:** Check out [`backend/storage/sample_template.mp4`](backend/storage/sample_template.mp4) to see a sample generated video!

> **No Docker, no cloud accounts needed.** The app runs in Demo Mode automatically.

### Prerequisites
- **Node.js** v18+ — [Download](https://nodejs.org)
- **Python** 3.9+ — [Download](https://python.org)

### 1 — Clone the repo

```bash
git clone https://github.com/webdevkaif/Qoneqt-Creator-AI.git
cd Qoneqt-Creator-AI
```

### 2 — Install dependencies & start everything

```bash
npm install          # installs root concurrently helper
npm run install:all  # installs frontend + backend deps
npm run dev          # starts both servers simultaneously
```

That's it! Open your browser:

| Service | URL |
|---------|-----|
| 🌐 **Frontend** | http://localhost:3000 |
| 🔧 **Backend API** | http://localhost:8000 |
| 📖 **Swagger Docs** | http://localhost:8000/api/docs |

> **Demo Mode** is active by default — no API keys required. The app uses local mock data for AI generation.

---

## 🔑 Enable Real AI (Optional)

To use GPT-4o scripts, DALL-E 3 images, and OpenAI TTS:

```bash
cp backend/.env backend/.env.local   # already created for you
```

Open `backend/.env` and fill in:

```env
OPENAI_API_KEY=sk-...         # enables real AI generation
ELEVENLABS_API_KEY=...        # (optional) better TTS voices
STABILITY_API_KEY=...         # (optional) alternative image gen
```

Restart the backend — it auto-detects keys and switches out of Demo Mode.

---

## 🛠 Manual Start (per-terminal)

If you prefer running services individually:

**Terminal 1 — Backend (FastAPI)**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend (Next.js)**
```bash
cd frontend
npm install
npm run dev
```

**Terminal 3 — Background Worker (Optional — needs Redis)**
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

> Without Redis, tasks run synchronously (still works, just slower).

---

## 🐳 Docker Setup (Full Stack)

For MongoDB + Redis + everything in one command:

```bash
# 1. Copy and fill environment file
cp .env.example backend/.env

# 2. Launch full stack
docker-compose up --build
```

Services launched automatically:
- MongoDB on `localhost:27017`
- Redis on `localhost:6379`
- FastAPI backend on `http://localhost:8000`
- Celery worker (background jobs)
- Next.js frontend on `http://localhost:3000`

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Script Generation** | GPT-4o creates scene-by-scene scripts from your topic |
| 🎨 **AI Image Generation** | DALL-E 3 or Stability AI generates visuals per scene |
| 🔊 **AI Narration (TTS)** | OpenAI TTS or ElevenLabs voices narrate each scene |
| 🎬 **FFmpeg Video Rendering** | Assembles scenes into a final MP4 with subtitles |
| 🌐 **Qoneqt Publishing** | Publishes video directly to Qoneqt Global Feed |
| 🔐 **JWT Auth** | Secure cookie-based authentication with refresh tokens |
| 📊 **Job Queue** | Celery + Redis for non-blocking background processing |
| 🧊 **Demo Mode** | Full app experience with no API keys required |

---

## 📐 Tech Stack

```
Frontend       Next.js 14 · TypeScript · React Context · Axios · Lucide Icons
Backend        FastAPI · Python 3.9 · Pydantic v2 · Beanie (async MongoDB ODM)
Database       MongoDB (motor) · mongomock-motor (in-memory fallback)
Queue          Celery · Redis (optional — eager fallback when unavailable)
Media          FFmpeg · Pillow
Auth           JWT (python-jose) · bcrypt
Storage        Local filesystem · AWS S3 (configurable)
Infrastructure Docker · Docker Compose
```

---

## 📖 API Reference

Interactive docs: **http://localhost:8000/api/docs**

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login, receive JWT cookie |
| `GET`  | `/api/v1/auth/me` | Get current user |
| `POST` | `/api/v1/auth/logout` | Clear auth cookies |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/projects` | Create project |
| `GET`  | `/api/v1/projects` | List your projects |
| `GET`  | `/api/v1/projects/{id}` | Get project details |
| `PATCH`| `/api/v1/projects/{id}` | Update project |

### Generation (AI Pipeline)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/generate/script/{id}` | Generate script via LLM |
| `POST` | `/api/v1/generate/visuals/{id}` | Generate scene images |
| `POST` | `/api/v1/generate/narration/{id}` | Generate TTS audio |
| `POST` | `/api/v1/generate/render/{id}` | Render final MP4 |
| `GET`  | `/api/v1/generate/jobs/{jobId}` | Poll job progress |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/system/health` | Health check + provider status |

---

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

> Tests use `mongomock-motor` so no real MongoDB needed.

---

## 🚢 Deployment

### Frontend → Vercel
```
1. Import the GitHub repo on vercel.com
2. Set Root Directory: frontend
3. Add env var: NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### Backend → Render / Railway / Cloud Run
```
1. Deploy backend/ directory as a Docker service
2. Start command: uvicorn app.main:app --host 0.0.0.0 --port 8000
3. Add all env vars from backend/.env
4. Connect to managed MongoDB Atlas + Redis Cloud
```

---

## 📁 Project Structure

```
Qoneqt-Creator-AI/
├── frontend/                 # Next.js 14 App
│   ├── app/
│   │   ├── auth/             # Login / Register pages
│   │   ├── dashboard/        # Project dashboard
│   │   ├── studio/           # Video creation studio
│   │   └── settings/         # User settings
│   ├── contexts/             # AuthContext
│   └── lib/api.ts            # Axios API client
│
├── backend/                  # FastAPI App
│   ├── app/
│   │   ├── api/routes/       # auth, projects, generation, publish, system
│   │   ├── core/             # config, security, database
│   │   ├── models/           # Beanie ODM models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── workers/          # Celery tasks
│   │   ├── adapters/         # AI provider factory (demo/real)
│   │   └── utils/            # storage, ffmpeg helpers
│   ├── tests/                # pytest test suite
│   ├── requirements.txt
│   └── .env                  # ← your local env file
│
├── docker-compose.yml
├── .vscode/settings.json     # IDE Python interpreter config
└── package.json              # Root dev runner (concurrently)
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT © [webdevkaif](https://github.com/webdevkaif)

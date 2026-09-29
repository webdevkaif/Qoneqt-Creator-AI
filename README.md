# Qoneqt Creator AI

Qoneqt Creator AI is an AI-powered full-stack web application designed to transform topics, prompts, and ideas into polished, community-specific short videos ready for the Qoneqt Global Feed.

## 🚀 Features

- **End-to-End AI Pipeline**: Generates scripts, storyboards, voice-overs, subtitles, and visual assets automatically.
- **Provider Agnostic**: Out-of-the-box support for OpenAI (GPT-4o, DALL-E 3, TTS-1) and a seamless "Demo Mode" for local development without API keys.
- **FFmpeg Engine**: Assembles scene assets, crops videos, applies subtitles, and normalizes audio locally.
- **Advanced Job Queue**: Background processing with Celery and Redis to handle long-running AI and rendering tasks.
- **Premium Frontend**: Next.js 14 App Router, React Context for Auth, and Tailwind CSS for a dark-mode glassmorphic aesthetic.
- **Honest Qoneqt Integration**: Provides manual copy-paste workflows if official APIs aren't provided, without faking success.

## 🛠 Tech Stack

- **Frontend**: Next.js (TypeScript), React, Tailwind CSS, Lucide Icons, Axios.
- **Backend**: FastAPI, Python 3.11, Pydantic, Beanie (MongoDB async ODM).
- **Workers**: Celery, Redis.
- **Media**: FFmpeg.
- **Infrastructure**: Docker, Docker Compose.

---

## 💻 Local Development Setup

### Prerequisites
- Docker and Docker Compose
- Node.js (v18+)
- (Optional) FFmpeg installed locally if you want to run backend without Docker.

### 1. Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and configure your API keys. 
   - **Demo Mode**: If you leave `OPENAI_API_KEY` blank, the app runs in Demo Mode, generating local placeholder assets and mock scripts.
   - **Production Mode**: Fill in `OPENAI_API_KEY` to use GPT-4o, DALL-E 3, and OpenAI TTS.

### 2. Start Services (Docker)

To run the entire stack (MongoDB, Redis, Backend API, Celery Worker, and Next.js Frontend) using Docker:

```bash
docker-compose up --build
```

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/api/docs`

### 3. Running Services Locally (Without Docker)

You can run both the frontend and backend simultaneously using the provided root `package.json` script. This handles installing both python and node dependencies, and running them concurrently.

**Step 1: Install All Dependencies**
```bash
npm install
npm run install:all
```

**Step 2: Start Both Servers Simultaneously**
```bash
npm run dev
```

This starts:
- **Frontend** at `http://localhost:3000`
- **Backend API** at `http://localhost:8000`

If you have Redis available and want to run the background Celery workers (not strictly required if eager tasks are enabled):
**Worker (Optional Terminal)**:
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
```

---

## 🧪 Testing

The backend includes a comprehensive pytest suite covering authentication, API routing, MongoDB integration, background job queuing, and file storage.

To run the backend tests:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Tests require active MongoDB/Redis on localhost
pytest tests/ -v
```

---

## 📖 API Usage

The backend exposes a fully documented REST API. Access the Swagger UI at `http://localhost:8000/api/docs`.

### Key Endpoints:
- `POST /api/v1/auth/register`: Create a new user. Returns JWT cookies.
- `POST /api/v1/projects`: Create a video project draft.
- `POST /api/v1/generate/script/{id}`: Dispatch a background Celery job to generate a script via LLM.
- `GET /api/v1/generate/jobs/{id}`: Poll Celery task progress.
- `POST /api/v1/generate/render/{id}`: Dispatch FFmpeg assembly job.
- `POST /api/v1/publish/{id}`: Publish completed video.

---

## 🚢 Deployment Instructions

### 1. Frontend (Vercel)
The Next.js frontend is optimized for deployment on Vercel.
1. Push the repository to GitHub.
2. Import the `frontend` directory as a new Vercel project.
3. Set the Environment Variable:
   - `NEXT_PUBLIC_API_URL`: Your deployed backend URL (e.g., `https://api.yourdomain.com`)

### 2. Backend & Worker (Render / Railway / AWS / GCP)
The backend requires a platform that supports persistent disk (for storage) and background processes (Celery), plus FFmpeg.

**Recommended Setup (Docker)**:
Deploy the provided `backend/Dockerfile` to a container service (e.g., Google Cloud Run, AWS ECS, or Render).
- **Web Service**: Command `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Worker Service**: Command `celery -A app.workers.celery_app worker --loglevel=info`

*Note: Ensure both services connect to the same managed MongoDB and Redis instances, and share a storage volume or configure the S3 backend.*

### 3. Cloud Storage (Production)
For production, local file storage is insufficient. 
Update `.env` to use S3-compatible storage:
```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket
```
*(You will need to implement the S3 boto3 upload logic inside `app/utils/storage.py` where the current local file write happens).*

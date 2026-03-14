# X Stories Homepage

A desktop-first logged-out homepage prototype for X.com that surfaces emerging stories from recent public posts.

The goal of this project is to make the logged-out homepage feel more like a modern internet news front page by clustering public posts into story cards with headlines and summaries, while still supporting the sign-in and sign-up funnel.

WEBSITE: https://x-homepage-preview-9knbeyxml-samarth217s-projects.vercel.app/

## What it does

* Ingests a batch of recent public-post samples
* Uses Grok to cluster posts into emerging stories
* Generates a headline and short summary for each story
* Renders a desktop-first logged-out homepage
* Supports refreshing the homepage over time with newly sampled posts

## Stack

### Backend

* Python
* FastAPI
* SQLite
* Requests

### Frontend

* Next.js
* TypeScript
* Tailwind CSS

## Architecture

The project is split into a small FastAPI backend and a Next.js frontend.

The backend reads post data from a local sample pool, selects a fresh subset on each refresh, stores posts in SQLite, and runs a story-generation pipeline. That pipeline uses Grok to cluster posts into story groups and generate a homepage-friendly headline and summary for each group. If Grok is unavailable or returns unusable output, the backend falls back gracefully so the homepage remains demoable.

The frontend fetches stories from the backend and renders:

* a featured story
* a brief side rail
* a grid of additional story cards
* a refresh action that reruns the backend pipeline and reloads the page

## API

* `GET /health` — health check
* `POST /refresh` — reruns ingestion and story generation
* `GET /stories` — returns the current homepage stories

## Local setup

### 1. Clone the repo

```bash
git clone https://github.com/Samarth217/X-homepage-preview.git
cd x-homepage-takehome
```

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Set backend environment variables

```bash
export XAI_API_KEY=your_xai_api_key
export GROK_MODEL=grok-4-latest
```

### 4. Start the backend

```bash
uvicorn backend.app.main:app --reload
```

### 5. Set frontend environment variables

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### 6. Install frontend dependencies

```bash
cd frontend
npm install
```

### 7. Start the frontend

```bash
npm run dev
```

Then open `http://localhost:3000`.

## Environment variables

### Backend

* `XAI_API_KEY` — required for Grok story clustering and headline generation
* `GROK_MODEL` — optional model override
* `GROK_API_BASE_URL` — optional API base URL override

### Frontend

* `NEXT_PUBLIC_API_BASE_URL` — backend base URL used by the frontend, for example:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Notes and tradeoffs

This prototype keeps the architecture intentionally small and demoable.

For the prototype, the ingestion layer currently reads from a curated public-post sample pool rather than a live X ingestion source. On refresh, the backend samples a fresh batch of posts, reclusters them with Grok, and rewrites the homepage story set. This keeps the experience dynamic while keeping the system small enough for a take-home prototype.

The backend includes graceful fallback behavior so the homepage can still refresh and remain populated if Grok output is unavailable or invalid.

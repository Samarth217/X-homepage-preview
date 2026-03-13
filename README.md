# X Stories Homepage

A desktop-first logged-out homepage prototype for X.com that surfaces emerging stories from recent public posts.

The goal of this project is to make the logged-out homepage feel more like a modern internet news front page by clustering public posts into story cards with headlines and summaries, while still supporting the sign-in and sign-up funnel.

## What it does

- ingests a batch of recent public-post samples
- uses Grok to cluster posts into emerging stories
- generates a headline and short summary for each story
- renders a desktop-first logged-out homepage
- supports refreshing the homepage over time with newly sampled posts

## Stack

### Backend
- Python
- FastAPI
- SQLite
- Requests

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

## Architecture

The project is split into a small FastAPI backend and a Next.js frontend.

The backend reads post data from a local sample pool, selects a fresh subset on each refresh, stores posts in SQLite, and runs a story-generation pipeline. That pipeline uses Grok to cluster posts into story groups and generate a homepage-friendly headline and summary for each group. If Grok is unavailable or returns unusable output, the backend falls back gracefully so the homepage remains demoable.

The frontend fetches stories from the backend and renders:
- a featured story
- a brief side rail
- a grid of additional story cards
- a refresh action that reruns the backend pipeline and reloads the page

## API

- `GET /health` — health check
- `POST /refresh` — reruns ingestion and story generation
- `GET /stories` — returns the current homepage stories

## Local setup

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
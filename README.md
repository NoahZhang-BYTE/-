# Challenge Cup Interview Tasks

This repository contains complete implementations for both interview questions, plus a bonus frontend console.

## Projects

- `q1-bilibili-downloader`: Bilibili video downloader script
- `q2-ai-chat-pipeline`: MySQL + GLM + `result.json` automation pipeline
- `bonus-web-console`: Web UI control panel for Q1 and Q2 (bonus item)

## Directory Structure

```text
challengecup-interview/
├─ q1-bilibili-downloader/
│  ├─ README.md
│  ├─ requirements.txt
│  └─ download_bilibili.py
├─ q2-ai-chat-pipeline/
│  ├─ README.md
│  ├─ .env.example
│  ├─ requirements.txt
│  ├─ process_chat_logs.py
│  └─ result.json
└─ bonus-web-console/
   ├─ README.md
   ├─ requirements.txt
   ├─ app.py
   └─ templates/
      └─ index.html
```

## Quick Start

1. Create and activate Python virtual environment.
2. Install dependencies in each subproject.
3. Configure `.env` for Q2 (set `GLM_API_KEY`).
4. Run scripts directly, or launch bonus web console.

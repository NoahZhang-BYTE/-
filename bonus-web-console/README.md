# Bonus - Frontend Control Console

This is a lightweight web console for bonus points.  
It provides a single UI to run both interview tasks:

- Q1: Bilibili downloader
- Q2: MySQL + GLM processing pipeline

## Features

- Form-based controls for Q1/Q2
- Real-time command output panel
- `result.json` live preview
- Mobile-friendly responsive layout

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open:

- <http://127.0.0.1:7860>

## Notes

- The app invokes existing scripts:
  - `../q1-bilibili-downloader/download_bilibili.py`
  - `../q2-ai-chat-pipeline/process_chat_logs.py`
- For Q2 real mode, ensure `../q2-ai-chat-pipeline/.env` contains a valid `GLM_API_KEY`.

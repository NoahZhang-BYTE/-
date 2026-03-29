# 挑战杯开发团队面试题 - 两题实现

本仓库包含两道题目的可运行实现：

- `q1-bilibili-downloader`：Bilibili 视频下载工具
- `q2-ai-chat-pipeline`：MySQL + GLM + result.json 自动化处理程序

## 目录结构

```text
challengecup-interview/
├─ q1-bilibili-downloader/
│  ├─ README.md
│  ├─ requirements.txt
│  └─ download_bilibili.py
└─ q2-ai-chat-pipeline/
   ├─ README.md
   ├─ .env.example
   ├─ requirements.txt
   └─ process_chat_logs.py
```

## 快速开始

1. 分别进入各子目录安装依赖并运行。
2. 题2需要先配置 `.env` 中的 `GLM_API_KEY`。

## GitHub 提交流程建议

```bash
git init
git add .
git commit -m "feat: complete challenge cup interview tasks"
git branch -M main
git remote add origin <your_repo_url>
git push -u origin main
```

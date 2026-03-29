# 加分项 - 中文前端控制台

这是一个轻量的本地 Web 控制台，用于展示加分项。  
功能是把两道题统一到一个中文界面里操作。

## 功能

- 表单触发题目 1（Bilibili 下载）
- 表单触发题目 2（MySQL + GLM 处理）
- 页面实时展示命令输出
- 页面实时预览 `result.json`

## 安装

```bash
pip install -r requirements.txt
```

## 启动

```bash
python app.py
```

浏览器打开：

- <http://127.0.0.1:7860>

## 说明

- 控制台会调用已有脚本：
  - `../q1-bilibili-downloader/download_bilibili.py`
  - `../q2-ai-chat-pipeline/process_chat_logs.py`
- 若运行题目 2 真实模式，请先配置 `../q2-ai-chat-pipeline/.env` 中的 `GLM_API_KEY`。

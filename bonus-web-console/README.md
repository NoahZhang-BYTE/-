# 任务对话控制台

这是一个本地 Web 对话页面，用于统一操作两道题：

- 题目 1：Bilibili 视频下载
- 题目 2：MySQL + GLM + result.json 处理

## 交互方式

- 页面主区域为对话流（类似 Chat 风格）
- 输入框用于发起任务
- 所有可选参数默认折叠在输入框下方（点击展开）
- 页面内可直接查看执行日志与 `result.json` 预览

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

- 控制台调用已有脚本：
  - `../q1-bilibili-downloader/download_bilibili.py`
  - `../q2-ai-chat-pipeline/process_chat_logs.py`
- 运行题目 2 真实模式前，需先配置：
  - `../q2-ai-chat-pipeline/.env` 中的 `GLM_API_KEY`

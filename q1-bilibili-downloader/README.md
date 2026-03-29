# Q1 - Bilibili 视频下载工具

一个可直接运行的 B 站视频下载脚本。

## 运行环境

- Python 3.10+
- 建议系统：Windows / Linux / macOS

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动方式

```bash
python download_bilibili.py "https://www.bilibili.com/video/BVxxxxxxxxx"
```

常用参数：

- `-o, --output-dir`：下载目录（默认 `downloads`）
- `--cookie-file`：Cookie 文件路径（需要登录内容时使用）
- `--audio-only`：仅下载音频
- `--proxy`：代理地址

示例：

```bash
python download_bilibili.py "https://www.bilibili.com/video/BV1xx411c7mD" -o ./downloads
```

## 说明

- 底层基于 `yt-dlp`，支持自动选择视频与音频流并合并。
- 如果遇到会员视频或地区限制，可提供 `--cookie-file` 或 `--proxy`。

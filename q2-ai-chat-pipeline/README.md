# Q2 - MySQL + GLM + result.json 自动化处理程序

该项目实现以下完整链路：

1. 读取 `chat_logs_D` 中 `process_status=pending` 的消息
2. 调用 GLM-4.7-Flash 生成角色扮演回复
3. 严格提取并校验 JSON 字段：
   - `character_name`
   - `mood`
   - `reply_text`
4. 将结果写入本地 `result.json`
5. 将数据库记录状态更新为 `processed`（失败更新为 `failed`）

## 运行环境

- Python 3.10+
- 可访问 MySQL 与 GLM API
- GLM 文档：<https://docs.bigmodel.cn/cn/api/introduction>

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置环境变量

复制示例文件：

```bash
cp .env.example .env
```

至少需要修改：

- `GLM_API_KEY`

## 启动命令

```bash
python process_chat_logs.py --result-file result.json --limit 20
```

常用参数：

- `--character-name`：自定义扮演角色名（默认 `星语陪伴师`）
- `--dry-run`：不修改数据库状态（调试）
- `--mock`：不调用 GLM，生成模拟回复（本地联调）
- `--env-file`：指定 `.env` 路径

## 输出格式

`result.json` 为数组，每条记录严格包含：

```json
{
  "character_name": "星语陪伴师",
  "mood": "温和",
  "reply_text": "我听到了你的想法..."
}
```

## 错误处理

- 数据库连接失败会直接退出并输出日志
- 单条消息处理失败不会影响其他记录
- 失败记录状态写回 `failed`，避免无限重试
